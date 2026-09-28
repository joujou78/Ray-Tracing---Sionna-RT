from fastapi import APIRouter, Depends, Query
from clickhouse_connect.driver.client import Client

from app.api.deps import get_ch_client, get_current_user
from app.schemas.log_event import LogSearchResponse
from app.services import log_search_service

router = APIRouter(prefix="/logs", tags=["logs"])

# Read-only investigation view -- same access level as /devices.
_authenticated = Depends(get_current_user)


@router.get("/search", response_model=LogSearchResponse)
async def search_logs(
    _user=_authenticated,
    client: Client = Depends(get_ch_client),
    hours: int = Query(24, ge=1, le=log_search_service.MAX_HOURS),
    source_ip: str | None = None,
    hostname: str | None = None,
    severity: str | None = None,
    program: str | None = None,
    predicted_category: str | None = None,
    is_anomaly: bool | None = None,
    q: str | None = Query(None, description="Substring match against the log message"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=log_search_service.MAX_PAGE_SIZE),
):
    return log_search_service.search_events(
        client,
        hours=hours,
        source_ip=source_ip,
        hostname=hostname,
        severity=severity,
        program=program,
        predicted_category=predicted_category,
        is_anomaly=is_anomaly,
        q=q,
        page=page,
        page_size=page_size,
    )
