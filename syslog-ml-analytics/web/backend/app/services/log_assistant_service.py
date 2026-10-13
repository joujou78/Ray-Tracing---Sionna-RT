"""Log Assistant: semantic search over syslog events (embeddings computed
and indexed into OpenSearch by ml/log_assistant_indexer.py) plus an LLM
(Ollama) that answers questions grounded only in the retrieved log
excerpts.

Deliberately does NOT let the model answer from its own general knowledge --
the system prompt instructs it to say so plainly when the retrieved
excerpts don't contain the answer, rather than guess. This matches the
project's existing "resolution_method is always labeled, nothing pretends
to know a hostname it doesn't" philosophy (see
syslog-ml-analytics/README.md's "Why this design" section).
"""
import httpx
from opensearchpy import OpenSearch

from app.core.config import settings
from app.ollama_client import chat, embed
from app.schemas.log_assistant import AskResponse, LogAssistantQuery, LogMatch, SemanticSearchResponse

# How many of the nearest log entries to retrieve per question. Not
# user-configurable -- a fixed, small context window keeps the chat prompt
# short enough for fast CPU-only inference.
TOP_K = 8

_SOURCE_FIELDS = ["event_time", "hostname", "severity", "program", "message", "predicted_category", "is_anomaly"]

_SYSTEM_PROMPT = (
    "You are a syslog analysis assistant. Answer ONLY using the log excerpts "
    "given below -- they are the complete evidence available to you. If the "
    "excerpts don't contain enough information to answer, say so plainly "
    "instead of guessing. Be concise and reference specific hostnames/times "
    "where relevant."
)


def _knn_search(os_client: OpenSearch, embedding: list[float], k: int) -> list[LogMatch]:
    response = os_client.search(
        index=settings.opensearch_index,
        body={
            "size": k,
            "query": {"knn": {"embedding": {"vector": embedding, "k": k}}},
            "_source": _SOURCE_FIELDS,
        },
    )
    return [LogMatch(score=hit["_score"], **hit["_source"]) for hit in response["hits"]["hits"]]


def _build_context(matches: list[LogMatch]) -> str:
    if not matches:
        return "(no matching log entries found)"
    lines = [
        f"- [{m.event_time}] {m.hostname} ({m.severity}/{m.program}, category={m.predicted_category}"
        f"{', ANOMALY' if m.is_anomaly else ''}): {m.message}"
        for m in matches
    ]
    return "\n".join(lines)


async def semantic_search(
    os_client: OpenSearch, ollama: httpx.AsyncClient, query: LogAssistantQuery
) -> SemanticSearchResponse:
    embedding = await embed(ollama, query.question)
    return SemanticSearchResponse(items=_knn_search(os_client, embedding, TOP_K))


async def ask(os_client: OpenSearch, ollama: httpx.AsyncClient, query: LogAssistantQuery) -> AskResponse:
    embedding = await embed(ollama, query.question)
    matches = _knn_search(os_client, embedding, TOP_K)

    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": f"Log excerpts:\n{_build_context(matches)}\n\nQuestion: {query.question}"},
    ]
    answer = await chat(ollama, messages)
    return AskResponse(answer=answer, sources=matches)
