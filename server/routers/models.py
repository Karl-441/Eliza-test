from fastapi import APIRouter, Depends, Query
from server.middleware.auth import verify_api_key
from server.core.models_registry import list_models

router = APIRouter()

@router.get("/", dependencies=[Depends(verify_api_key)])
def get_models(q: str = Query(default="", description="筛选关键词")):
    return list_models(q)
