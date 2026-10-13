import logging

from fastapi import APIRouter, Depends, HTTPException, status
from httpx import AsyncClient, HTTPError
from opensearchpy import OpenSearch
from opensearchpy.exceptions import OpenSearchException

from app.api.deps import get_current_user, get_ollama_client, get_os_client
from app.schemas.log_assistant import AskResponse, LogAssistantQuery, SemanticSearchResponse
from app.services import log_assistant_service

log = logging.getLogger("log_assistant_routes")

router = APIRouter(prefix="/log-assistant", tags=["log-assistant"])

# Read-only, same as /logs -- any authenticated user can ask. The LLM call
# is slow (CPU inference), not privileged -- that's a performance concern
# for whoever asks, not a reason to gate it.
_authenticated = Depends(get_current_user)

# OpenSearch/Ollama being unreachable or misconfigured isn't the caller's
# fault -- 502 with the real error, rather than an opaque 500. A "succeeded"
# response with an unexpected shape (e.g. Ollama's JSON missing the
# ["message"]["content"] path) surfaces as KeyError/ValueError, not an
# HTTPError, so those are caught here too.
_UPSTREAM_ERRORS = (HTTPError, OpenSearchException, KeyError, ValueError)


def _upstream_error(exc: Exception) -> HTTPException:
    log.exception("Log Assistant upstream error (returning 502 to caller)")
    return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Log Assistant backend error: {exc}")


@router.post("/search", response_model=SemanticSearchResponse)
async def search(
    payload: LogAssistantQuery,
    _user=_authenticated,
    os_client: OpenSearch = Depends(get_os_client),
    ollama: AsyncClient = Depends(get_ollama_client),
):
    try:
        return await log_assistant_service.semantic_search(os_client, ollama, payload)
    except _UPSTREAM_ERRORS as exc:
        raise _upstream_error(exc)


@router.post("/ask", response_model=AskResponse)
async def ask(
    payload: LogAssistantQuery,
    _user=_authenticated,
    os_client: OpenSearch = Depends(get_os_client),
    ollama: AsyncClient = Depends(get_ollama_client),
):
    try:
        return await log_assistant_service.ask(os_client, ollama, payload)
    except _UPSTREAM_ERRORS as exc:
        raise _upstream_error(exc)
