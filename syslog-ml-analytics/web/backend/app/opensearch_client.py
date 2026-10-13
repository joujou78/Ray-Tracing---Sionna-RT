"""Lazy singleton OpenSearch client, the same shape as clickhouse_client.py.

The index itself (mapping, knn settings) is created by
ml/log_assistant_indexer.py -- the writer owns the schema; this client is
only ever used here to query it.
"""
from opensearchpy import OpenSearch

from app.core.config import settings

_client: OpenSearch | None = None


def get_opensearch_client() -> OpenSearch:
    global _client
    if _client is None:
        _client = OpenSearch(
            hosts=[{"host": settings.opensearch_host, "port": settings.opensearch_port}],
            use_ssl=False,
        )
    return _client
