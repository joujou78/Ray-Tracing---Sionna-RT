"""Thin async HTTP client for a local Ollama server -- used by the Log
Assistant for both embeddings (semantic search queries) and chat completion
(answering questions over retrieved log excerpts).

A lazy singleton httpx.AsyncClient, the same shape as clickhouse_client.py's
lazy client, but async: chat completion on CPU-only inference can take tens
of seconds and must not block the event loop for other requests the way a
sync call would.
"""
import httpx

from app.core.config import settings

_client: httpx.AsyncClient | None = None


def get_ollama_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(base_url=settings.ollama_host, timeout=settings.ollama_timeout_seconds)
    return _client


async def embed(client: httpx.AsyncClient, text: str) -> list[float]:
    response = await client.post("/api/embeddings", json={"model": settings.ollama_embed_model, "prompt": text})
    response.raise_for_status()
    return response.json()["embedding"]


async def chat(client: httpx.AsyncClient, messages: list[dict]) -> str:
    response = await client.post(
        "/api/chat",
        json={
            "model": settings.ollama_chat_model,
            "messages": messages,
            "stream": False,
            "options": {"num_predict": settings.ollama_num_predict},
        },
    )
    response.raise_for_status()
    return response.json()["message"]["content"]
