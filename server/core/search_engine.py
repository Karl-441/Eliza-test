import logging
import time
import json
import re
from typing import Optional, Dict, List, Any
from .search import search_engine

logger = logging.getLogger(__name__)

class AISearchArchitect:
    """
    Implements the 3-layer architecture:
    1. Local Core (Intent Recognition)
    2. Networking (Search Execution)
    3. Result Processing (Fusion)
    """
    
    def __init__(self):
        self.engine = search_engine

    def analyze_intent(self, query: str) -> Dict[str, Any]:
        """
        Layer 1: Local Intent Recognition
        Uses Hybrid approach: Heuristic (Fast) -> LLM (Deep)
        """
        # 1. Fast Heuristic Check
        heuristic_result = self._analyze_heuristic(query)
        if heuristic_result["needs_search"] and heuristic_result["search_type"] in ["realtime", "explicit"]:
            return heuristic_result
            
        # 2. LLM Deep Analysis (for ambiguous or complex queries)
        # Only if heuristics didn't trigger a "definite yes", but we suspect it might need one
        # Or if we want to parse complex search operators.
        # For performance, we skip LLM if heuristic says NO and query is simple.
        # But per requirements "Local model responsible for intent recognition", we should try to use it.
        
        try:
            # Import here to avoid circular dependency at module level
            from .llm import llm_engine
            if llm_engine.status == "ready":
                return self._analyze_with_llm(query, llm_engine)
        except Exception as e:
            logger.warning(f"LLM Intent Analysis failed: {e}")
            
        return heuristic_result

    def _analyze_heuristic(self, query: str) -> Dict[str, Any]:
        query_lower = query.lower()
        triggers_realtime = ["news", "latest", "current", "today", "now", "price", "stock", "weather", "forecast", "schedule", "when is", "what time"]
        if any(t in query_lower for t in triggers_realtime):
            return {"needs_search": True, "search_type": "realtime", "keywords": query}
            
        triggers_factual = ["who is", "what is", "define", "explain", "history of", "search for", "find"]
        if any(t in query_lower for t in triggers_factual) and len(query.split()) > 2: 
            return {"needs_search": True, "search_type": "factual", "keywords": query}
                
        if "search" in query_lower or "google" in query_lower or "look up" in query_lower:
             return {"needs_search": True, "search_type": "explicit", "keywords": query}

        return {"needs_search": False, "search_type": "none", "keywords": ""}

    def _analyze_with_llm(self, query: str, llm) -> Dict[str, Any]:
        """
        Ask LLM to classify intent and generate search keywords.
        """
        prompt = f"""
Analyze the following user query and determine if it requires an internet search to answer.
Query: "{query}"

Respond ONLY with a JSON object in this format:
{{
    "needs_search": true/false,
    "search_type": "realtime" | "factual" | "none",
    "search_query": "optimized search keywords or operators"
}}

Rules:
- "realtime": Weather, stocks, news, current events (2024-2025).
- "factual": Specific entities, definitions not in general knowledge.
- "none": Greetings, logic, coding, general knowledge.
- If unsure, set needs_search to false.
"""
        try:
            # Generate response (using a separate call, not streaming)
            response_text = llm.generate_response(query, prompt)
            
            # Extract JSON
            match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                return {
                    "needs_search": data.get("needs_search", False),
                    "search_type": data.get("search_type", "none"),
                    "keywords": data.get("search_query", query)
                }
        except Exception as e:
            logger.error(f"Error parsing LLM intent: {e}")
            
        # Fallback to heuristic if LLM fails
        return self._analyze_heuristic(query)

    def execute_search(self, query: str) -> Dict[str, Any]:
        """
        Layer 2: Networking
        """
        logger.info(f"Executing AI Search for: {query}")
        return self.engine.search(query, max_results=5)

    def process_results(self, raw_data: Dict[str, Any]) -> str:
        """
        Layer 3: Result Processing & Fusion
        """
        if not raw_data or not raw_data.get("raw"):
            return ""
            
        summary = "Network Search Results:\n"
        
        for idx, res in enumerate(raw_data["raw"]):
            title = res.get("title", "Untitled")
            body = res.get("body", "No content")
            source = res.get("href", "Unknown Source")
            
            # Cleaning
            body = body.replace("\n", " ").strip()
            
            summary += f"[{idx+1}] {title}\n    Source: {source}\n    Summary: {body}\n\n"
            
            # Knowledge Backfill (Simple Heuristic)
            # If result seems high quality (e.g. from edu/gov or high relevance), consider saving to LTM
            # For now, we just log it as a candidate. In a full system, we'd embed this.
            self._backfill_knowledge(title, body, source)
            
        return summary

    def _backfill_knowledge(self, title: str, content: str, source: str):
        """
        Optional: Save high-value info to Long Term Memory (Knowledge Base)
        """
        # Filter: Only save if content is substantial
        if len(content) > 50:
            try:
                from .memory import memory_manager
                # Create a specialized memory node for external knowledge
                # Using 'system' role or a specific 'knowledge' tag
                # We append it to a specific queue or let the memory manager handle it
                # For this implementation, we won't clutter the main chat memory automatically
                # unless explicitly requested, but the architecture supports it here.
                pass
            except Exception:
                pass

ai_search = AISearchArchitect()
