"""
Real-time pipeline: Kafka/Redpanda -> Drain3 template mining -> ML category
classifier -> ClickHouse.

Runs continuously as the `classifier` service in docker-compose.yml. If
MODEL_PATH doesn't exist yet (no classifier trained yet), falls back to the
weak-supervision rules in labeling_rules.py so the pipeline is useful from
day one, then swap in the trained model once train_classifier.py has run.
"""
import json
import logging
import os
import time
from datetime import datetime, timezone

import clickhouse_connect
import joblib
from drain3 import TemplateMiner
from drain3.template_miner_config import TemplateMinerConfig
from kafka import KafkaConsumer

from labeling_rules import weak_label, severity_rank

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("consumer")

KAFKA_BROKER = os.environ.get("KAFKA_BROKER", "localhost:9092")
KAFKA_TOPIC = os.environ.get("KAFKA_TOPIC", "syslog.raw")
CLICKHOUSE_HOST = os.environ.get("CLICKHOUSE_HOST", "localhost")
CLICKHOUSE_PORT = int(os.environ.get("CLICKHOUSE_PORT", "8123"))
MODEL_PATH = os.environ.get("MODEL_PATH", "/models/classifier.joblib")
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "500"))
BATCH_FLUSH_SECONDS = float(os.environ.get("BATCH_FLUSH_SECONDS", "2"))

INSERT_COLUMNS = [
    "event_time", "host", "facility", "severity", "severity_num", "program",
    "pid", "message", "template_id", "template", "predicted_category",
    "predicted_confidence", "is_anomaly", "raw",
]


def load_classifier():
    if os.path.exists(MODEL_PATH):
        log.info("Loaded trained classifier from %s", MODEL_PATH)
        return joblib.load(MODEL_PATH)
    log.warning("No trained model at %s yet — using weak-supervision rules until one is trained", MODEL_PATH)
    return None


def build_template_miner():
    config = TemplateMinerConfig()
    config.load(None)
    config.profiling_enabled = False
    return TemplateMiner(config=config)


def classify(model, message):
    if model is not None:
        try:
            proba = model.predict_proba([message])[0]
            idx = proba.argmax()
            return model.classes_[idx], float(proba[idx])
        except Exception:
            log.exception("Classifier inference failed, falling back to rules")
    return weak_label(message), 0.0


def parse_record(raw_bytes):
    try:
        record = json.loads(raw_bytes.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        return None
    if "message" not in record:
        return None
    return record


def to_row(record, miner, model):
    message = record.get("message", "")
    cluster = miner.add_log_message(message)
    timestamp = record.get("timestamp")
    try:
        event_time = datetime.fromisoformat(timestamp) if timestamp else datetime.now(timezone.utc)
    except ValueError:
        event_time = datetime.now(timezone.utc)

    category, confidence = classify(model, message)
    severity = record.get("severity", "info")

    pid_raw = record.get("pid")
    try:
        pid = int(pid_raw) if pid_raw not in (None, "") else None
    except (TypeError, ValueError):
        pid = None

    return [
        event_time,
        record.get("host", "unknown"),
        record.get("facility", "unknown"),
        severity,
        severity_rank(severity),
        record.get("program", "unknown"),
        pid,
        message,
        str(cluster["cluster_id"]),
        cluster["template_mined"],
        category,
        confidence,
        0,
        record.get("raw", message),
    ]


def main():
    model = load_classifier()
    miner = build_template_miner()

    client = clickhouse_connect.get_client(host=CLICKHOUSE_HOST, port=CLICKHOUSE_PORT)

    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BROKER,
        auto_offset_reset="latest",
        enable_auto_commit=True,
        group_id="syslog-ml-classifier",
    )

    log.info("Consuming from %s@%s -> ClickHouse %s:%s", KAFKA_TOPIC, KAFKA_BROKER, CLICKHOUSE_HOST, CLICKHOUSE_PORT)

    batch = []
    last_flush = time.monotonic()

    for message in consumer:
        record = parse_record(message.value)
        if record is None:
            continue

        batch.append(to_row(record, miner, model))

        should_flush = len(batch) >= BATCH_SIZE or (time.monotonic() - last_flush) >= BATCH_FLUSH_SECONDS
        if should_flush and batch:
            try:
                client.insert("syslog_ml.events", batch, column_names=INSERT_COLUMNS)
            except Exception:
                log.exception("Failed to insert batch of %d rows", len(batch))
            batch = []
            last_flush = time.monotonic()


if __name__ == "__main__":
    main()
