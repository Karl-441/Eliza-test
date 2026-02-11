from fastapi import APIRouter, Depends, Query
from server.middleware.auth import verify_api_key
from server.core.models_registry import list_models

from server.core.i18n import I18N

router = APIRouter()

@router.get("/", dependencies=[Depends(verify_api_key)])
def get_models(q: str = Query(default="", description=I18N.t("query_desc_filter"))):
    return list_models(q)
