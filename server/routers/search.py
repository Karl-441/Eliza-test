from fastapi import APIRouter, Query
from typing import Optional
from server.core.search import search_engine
from server.core.monitor import audit_logger
from server.core.i18n import I18N

router = APIRouter(tags=["Search"])

@router.get("/search")
async def generic_search(q: str = Query(..., min_length=1), max_results: int = Query(3, ge=1, le=10)):
    data = search_engine.search(q, max_results=max_results)
    return data

@router.get("/search/weather")
async def weather_today(city: Optional[str] = Query(None)):
    suffix = I18N.t("search_weather_suffix")
    q = f"{city} {suffix}" if city else suffix
    data = search_engine._weather_today(q)
    return data

@router.get("/history")
async def get_search_history():
    return search_engine.history.history

