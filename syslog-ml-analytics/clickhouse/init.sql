CREATE DATABASE IF NOT EXISTS syslog_ml;

CREATE TABLE IF NOT EXISTS syslog_ml.events
(
    event_time          DateTime64(3),
    received_at         DateTime64(3) DEFAULT now64(3),
    host                LowCardinality(String),
    facility            LowCardinality(String),
    severity            LowCardinality(String),
    severity_num        UInt8,
    program             LowCardinality(String),
    pid                 Nullable(UInt32),
    message             String,
    template_id         String,
    template             String,
    predicted_category  LowCardinality(String),
    predicted_confidence Float32,
    is_anomaly          UInt8 DEFAULT 0,
    raw                 String
)
ENGINE = MergeTree
PARTITION BY toYYYYMMDD(event_time)
ORDER BY (event_time, host, severity)
TTL toDateTime(event_time) + INTERVAL 90 DAY
SETTINGS index_granularity = 8192;

-- Pre-aggregated per-minute rollup so Grafana panels stay fast even once
-- `events` holds hundreds of millions of rows.
CREATE MATERIALIZED VIEW IF NOT EXISTS syslog_ml.events_by_minute
ENGINE = SummingMergeTree
PARTITION BY toYYYYMMDD(minute)
ORDER BY (minute, host, severity, predicted_category)
AS
SELECT
    toStartOfMinute(event_time) AS minute,
    host,
    severity,
    predicted_category,
    count()                      AS event_count,
    sum(is_anomaly)              AS anomaly_count
FROM syslog_ml.events
GROUP BY minute, host, severity, predicted_category;
