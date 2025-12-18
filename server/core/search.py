import time
import json
import re
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import requests
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

BASE_DIR = Path(__file__).resolve().parent.parent
HISTORY_FILE = str(BASE_DIR / "data" / "search_history.json")

class SearchHistory:
    def __init__(self):
        self.history = []
        self.load()
    
    def load(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    self.history = json.load(f)
            except:
                pass
                
    def add(self, query, summary):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "summary": summary[:200] + "..." if len(summary) > 200 else summary
        }
        self.history.insert(0, entry)
        if len(self.history) > 100:
            self.history = self.history[:100]
        self.save()
        
    def save(self):
        try:
            os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=4, ensure_ascii=False)
        except:
            pass

class SearchEngine:
    def __init__(self):
        self.ddgs = DDGS()
        self.history = SearchHistory()
        self.last_request_time = 0
        self.request_count = 0
        self.minute_start = 0
        self.cache: Dict[str, tuple[float, dict]] = {}  # Key: query, Value: (timestamp, result)
        self.cache_ttl = 300  # 5 minutes
        self.weather_ttl = 600  # 10 minutes
        
        # Keyword Library for Auto-Trigger (Representative subset)
        self.keywords = {
            "weather": ["天气", "气温", "下雨", "forecast", "temperature", "weather"],
            "news": ["新闻", "头条", "news", "headline", "latest"],
            "stock": ["股票", "股价", "大盘", "stock", "price", "market"],
            "exchange": ["汇率", "兑换", "exchange rate", "currency", "usd", "cny"],
            "fact": ["是谁", "什么", "why", "who is", "what is", "how to", "搜索", "search", "lookup", "find"]
        }
        try:
            from server.core.monitor import audit_logger
            self.audit_logger = audit_logger
        except Exception:
            self.audit_logger = None

    def _check_rate_limit(self):
        now = time.time()
        if now - self.minute_start > 60:
            self.minute_start = now
            self.request_count = 0
        
        if self.request_count >= 5:
            return False
        
        self.request_count += 1
        return True

    def should_search(self, query: str) -> bool:
        query_lower = query.lower()
        for category, terms in self.keywords.items():
            for term in terms:
                if term in query_lower:
                    return True
        return False
    
    def _log_failure(self, action: str, details: str):
        try:
            if self.audit_logger:
                self.audit_logger.log(action, details)
        except Exception:
            pass
    
    def _extract_city(self, query: str) -> Optional[str]:
        text = query.strip()
        # Simple patterns: "上海天气", "Beijing weather", "Weather in Tokyo"
        m = re.search(r"(?:天气|weather|forecast)[\s]*在?([\u4e00-\u9fa5A-Za-z\-\s]+)", text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
        m2 = re.search(r"([\u4e00-\u9fa5A-Za-z\-\s]+)[\s]*(?:天气|weather|forecast)", text, re.IGNORECASE)
        if m2:
            return m2.group(1).strip()
        return None
    
    def _geocode(self, place: str) -> Optional[Dict[str, Any]]:
        try:
            url = "https://geocoding-api.open-meteo.com/v1/search"
            params = {"name": place, "count": 1, "language": "zh", "format": "json"}
            resp = requests.get(url, params=params, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("results"):
                    r = data["results"][0]
                    return {"name": r.get("name"), "lat": r.get("latitude"), "lon": r.get("longitude"), "country": r.get("country")}
        except Exception as e:
            self._log_failure("SEARCH_WEATHER_GEOCODE_FAIL", f"{place}: {e}")
        return None
    
    def _weather_today(self, query: str) -> dict:
        now = time.time()
        cache_key = f"weather::{query}"
        if cache_key in self.cache:
            ts, data = self.cache[cache_key]
            if now - ts < self.weather_ttl:
                return data
        city = self._extract_city(query) or "Shanghai"
        geo = self._geocode(city)
        if not geo:
            # Fallback: try DDG quick answers as auto-repair
            try:
                results = self.ddgs.text(f"{city} weather today", max_results=2)
                summary = "Weather (fallback):\n"
                for r in results or []:
                    summary += f"- {r.get('title')}: {r.get('body')}\n"
                data = {"summary": summary.strip(), "raw": results or [], "source": "duckduckgo"}
                self.cache[cache_key] = (now, data)
                self.history.add(query, data["summary"])
                return data
            except Exception as e:
                self._log_failure("SEARCH_WEATHER_FALLBACK_FAIL", f"{city}: {e}")
                return {"summary": f"Weather lookup failed for {city}.", "raw": [], "source": "error"}
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": geo["lat"],
                "longitude": geo["lon"],
                "current_weather": "true",
                "hourly": "temperature_2m,precipitation",
                "timezone": "auto"
            }
            # Retry
            for attempt in range(3):
                try:
                    resp = requests.get(url, params=params, timeout=6)
                    if resp.status_code == 200:
                        w = resp.json()
                        cw = w.get("current_weather", {})
                        temp = cw.get("temperature")
                        wind = cw.get("windspeed")
                        weathercode = cw.get("weathercode")
                        precip = None
                        hourly = w.get("hourly", {})
                        if hourly and "precipitation" in hourly:
                            precip = sum(hourly["precipitation"][:6]) if hourly.get("precipitation") else None
                        desc = f"{geo['name']} ({geo.get('country','')}) 当前气温 {temp}°C，风速 {wind} m/s"
                        if precip is not None:
                            desc += f"，预计未来6小时降水量 {precip} mm"
                        if weathercode is not None:
                            desc += f"，天气码 {weathercode}"
                        data = {
                            "summary": f"今日天气：{desc}",
                            "raw": {"geo": geo, "data": w},
                            "source": "open-meteo"
                        }
                        self.cache[cache_key] = (now, data)
                        self.history.add(query, data["summary"])
                        return data
                except Exception as e:
                    time.sleep(1)
                    if attempt == 2:
                        self._log_failure("SEARCH_WEATHER_API_FAIL", f"{city}: {e}")
                        break
        except Exception as e:
            self._log_failure("SEARCH_WEATHER_ERROR", f"{city}: {e}")
        return {"summary": f"Weather lookup failed for {city}.", "raw": [], "source": "error"}

    def search(self, query: str, max_results: int = 3) -> dict:
        # Check Cache
        now = time.time()
        if query in self.cache:
            timestamp, data = self.cache[query]
            if now - timestamp < self.cache_ttl:
                return data
        
        # Check Rate Limit
        if not self._check_rate_limit():
            return {"summary": "System Alert: Network request limit reached (5/min). Please wait.", "raw": []}

        # Weather path
        if any(term in query.lower() for term in self.keywords["weather"]):
            return self._weather_today(query)
        
        # Retry logic
        for attempt in range(3):
            try:
                results = self.ddgs.text(query, max_results=max_results)
                if not results:
                    return {"summary": "No search results found.", "raw": []}
                
                # De-duplication (by URL)
                seen_urls = set()
                unique_results = []
                for res in results:
                    if res['href'] not in seen_urls:
                        unique_results.append(res)
                        seen_urls.add(res['href'])
                
                summary = "Search Results:\n"
                for res in unique_results:
                    summary += f"- {res['title']}: {res['body']}\n"
                
                data = {"summary": summary, "raw": unique_results}
                
                # Update Cache
                self.cache[query] = (now, data)
                self.history.add(query, summary)
                return data
            except Exception as e:
                time.sleep(1) # Backoff
                if attempt == 2:
                    self._log_failure("SEARCH_GENERAL_FAIL", str(e))
                    return {"summary": f"Search failed after retries: {e}", "raw": []}
        return {"summary": "Search failed.", "raw": []}

search_engine = SearchEngine()
