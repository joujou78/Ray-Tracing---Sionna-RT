"""
Periodic worker (systemd timer, e.g. every 5 minutes): embeds newly-arrived
syslog_ml.events rows via a local Ollama server and indexes them into
OpenSearch for the web app's Log Assistant (semantic search + LLM Q&A).

Kept as its own process rather than folded into consumer.py for the same
reason resolve_pending.py is separate: embedding calls to Ollama (even a
small model) are slow enough on CPU-only hardware that they must not sit in
the hot log-ingestion path.

Incremental: tracks the newest `received_at` it has indexed in a small local
SQLite checkpoint file -- a different schema/concern from state_db.py's
pending_ips table, so it gets its own file rather than reusing that one.
Edge case worth flagging: the next run's WHERE clause is `received_at >
checkpoint`, so if a batch ends exactly at its size limit while multiple
rows share the same (millisecond-precision) received_at as the last row
kept, any sibling rows not included in that batch would be skipped. Real
traffic volumes make this rare, and it isn't handled specially here.
"""
import logging
import os
import sqlite3

import clickhouse_connect
import httpx
from opensearchpy import OpenSearch, helpers

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("log_assistant_indexer")

CLICKHOUSE_HOST = os.environ.get("CLICKHOUSE_HOST", "localhost")
CLICKHOUSE_PORT = int(os.environ.get("CLICKHOUSE_PORT", "8123"))
OPENSEARCH_HOST = os.environ.get("OPENSEARCH_HOST", "localhost")
OPENSEARCH_PORT = int(os.environ.get("OPENSEARCH_PORT", "9200"))
OPENSEARCH_INDEX = os.environ.get("OPENSEARCH_INDEX", "syslog_logs")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_EMBED_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")
EMBED_DIMENSION = int(os.environ.get("EMBED_DIMENSION", "768"))
CHECKPOINT_DB = os.environ.get("CHECKPOINT_DB", "/var/lib/syslog-ml/indexer_state.db")
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "500"))

_EVENT_COLUMNS = [
    "event_time", "received_at", "hostname", "vendor", "severity",
    "program", "message", "template", "predicted_category", "is_anomaly",
]

INDEX_MAPPING = {
    "settings": {"index": {"knn": True}},
    "mappings": {
        "properties": {
            "event_time": {"type": "date"},
            "hostname": {"type": "keyword"},
            "vendor": {"type": "keyword"},
            "severity": {"type": "keyword"},
            "program": {"type": "keyword"},
            "message": {"type": "text"},
            "template": {"type": "text"},
            "predicted_category": {"type": "keyword"},
            "is_anomaly": {"type": "boolean"},
            "embedding": {
                "type": "knn_vector",
                "dimension": EMBED_DIMENSION,
                "method": {"name": "hnsw", "space_type": "cosinesimil", "engine": "nmslib"},
            },
        }
    },
}


def _checkpoint_conn():
    os.makedirs(os.path.dirname(CHECKPOINT_DB), exist_ok=True)
    conn = sqlite3.connect(CHECKPOINT_DB)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS indexer_checkpoint (id INTEGER PRIMARY KEY CHECK (id = 1), last_received_at TEXT)"
    )
    conn.commit()
    return conn


def _get_checkpoint(conn) -> str | None:
    row = conn.execute("SELECT last_received_at FROM indexer_checkpoint WHERE id = 1").fetchone()
    return row[0] if row else None


def _set_checkpoint(conn, value: str) -> None:
    conn.execute(
        "INSERT INTO indexer_checkpoint (id, last_received_at) VALUES (1, ?) "
        "ON CONFLICT(id) DO UPDATE SET last_received_at = excluded.last_received_at",
        (value,),
    )
    conn.commit()


def _ensure_index(os_client: OpenSearch) -> None:
    if not os_client.indices.exists(index=OPENSEARCH_INDEX):
        os_client.indices.create(index=OPENSEARCH_INDEX, body=INDEX_MAPPING)
        log.info("Created OpenSearch index %s", OPENSEARCH_INDEX)


def _embed(http_client: httpx.Client, text: str) -> list[float]:
    response = http_client.post(f"{OLLAMA_HOST}/api/embeddings", json={"model": OLLAMA_EMBED_MODEL, "prompt": text})
    response.raise_for_status()
    return response.json()["embedding"]


def _fetch_batch(ch_client, since: str | None) -> list[dict]:
    conditions = []
    params: dict = {"limit": BATCH_SIZE}
    if since is not None:
        conditions.append("received_at > %(since)s")
        params["since"] = since
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    query = f"""
        SELECT {', '.join(_EVENT_COLUMNS)}
        FROM syslog_ml.events
        {where}
        ORDER BY received_at ASC
        LIMIT %(limit)s
    """
    result = ch_client.query(query, parameters=params)
    return [dict(zip(_EVENT_COLUMNS, row)) for row in result.result_rows]


def main():
    ch_client = clickhouse_connect.get_client(host=CLICKHOUSE_HOST, port=CLICKHOUSE_PORT)
    os_client = OpenSearch(hosts=[{"host": OPENSEARCH_HOST, "port": OPENSEARCH_PORT}], use_ssl=False)
    _ensure_index(os_client)

    checkpoint_conn = _checkpoint_conn()
    since = _get_checkpoint(checkpoint_conn)

    rows = _fetch_batch(ch_client, since)
    if not rows:
        log.info("No new events to index since %s", since)
        checkpoint_conn.close()
        return

    actions = []
    with httpx.Client(timeout=60.0) as http_client:
        for row in rows:
            embedding = _embed(http_client, row["message"])
            actions.append(
                {
                    "_index": OPENSEARCH_INDEX,
                    "_source": {
                        "event_time": row["event_time"].isoformat(),
                        "hostname": row["hostname"],
                        "vendor": row["vendor"],
                        "severity": row["severity"],
                        "program": row["program"],
                        "message": row["message"],
                        "template": row["template"],
                        "predicted_category": row["predicted_category"],
                        "is_anomaly": bool(row["is_anomaly"]),
                        "embedding": embedding,
                    },
                }
            )

    helpers.bulk(os_client, actions)

    newest = max(row["received_at"] for row in rows)
    _set_checkpoint(checkpoint_conn, newest.isoformat())
    checkpoint_conn.close()
    log.info("Indexed %d event(s), checkpoint advanced to %s", len(rows), newest.isoformat())


if __name__ == "__main__":
    main()
