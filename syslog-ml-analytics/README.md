# Syslog ML Analytics

A syslog analytics stack with its own database and ML classification layer,
sitting **alongside** your existing rsyslog/syslog-ng + LogAnalyzer setup
(it doesn't replace it — LogAnalyzer keeps working exactly as it does today).

Modeled on the same idea as vendor "ML-based syslog analytics" write-ups
(e.g. GeakMinds' post): ingest -> parse/normalize -> classify -> store ->
dashboard. This is a from-scratch open-source build of that pattern, not a
copy of any vendor's implementation — I could not fetch geakminds.com from
this environment (its domain is blocked by the sandbox's egress proxy), so
nothing here is based on that page's specific internals.

## Architecture

```
network devices --syslog--> rsyslog (existing) ----------> LogAnalyzer DB (unchanged)
                                  |
                                  +--omkafka (JSON copy)--> Redpanda (Kafka API)
                                                                   |
                                                          classifier (Python)
                                                          - Drain3 template mining
                                                          - ML category classifier
                                                                   |
                                                              ClickHouse
                                                                   |
                                                                Grafana
```

- **Redpanda**: Kafka-API-compatible broker, single binary — chosen over
  Kafka+Zookeeper because it's much lighter to run on one VM while still
  giving you a durable buffer between ingestion and processing at 10M+
  lines/day.
- **ClickHouse**: column-store for the parsed/classified events. At the
  "large" scale (500+ devices, 10M+ lines/day) it uses far less RAM than
  Elasticsearch/OpenSearch for the same aggregation queries, which is what
  Grafana will be running constantly.
- **classifier service**: consumes the raw JSON stream, mines recurring log
  *templates* with Drain3 (groups "interface GigabitEthernet0/1 down" and
  "interface GigabitEthernet0/2 down" into one template), predicts a
  **category** (AUTH / NETWORK / HARDWARE / SECURITY / SYSTEM / APPLICATION /
  CONFIG) per message, and writes structured rows to ClickHouse.
- **Grafana**: dashboards on top of ClickHouse — this is the piece your
  earlier "Grafana" ask maps onto.

## Honest limitations (read before relying on this)

- **No labeled training data exists yet.** `labeling_rules.py` uses generic
  keyword rules to bootstrap categories. Until you train on real labels (or
  at least review a sample of the weak-supervision output against your own
  devices' log formats), treat `predicted_category` as a rough sort, not a
  verified classification. Vendor-specific log formats (proprietary NOS,
  telecom equipment, etc.) will need rules/examples added to
  `CATEGORY_RULES`.
- **Anomaly detection is not implemented yet** — the schema has an
  `is_anomaly` column reserved for it, but per your priority this build
  focuses on classification first. A follow-up (rolling per-host/per-template
  rate z-scores against `events_by_minute`) is a natural next phase.
- The Grafana dashboard JSON was written against the current
  `grafana-clickhouse-datasource` plugin's SQL query format from
  documentation, not verified against a live Grafana instance from this
  session (no VM access here) — check it imports cleanly and adjust field
  names if the plugin version on your VM differs.
- Sizing (Redpanda 1 vCPU/1GB, etc.) is a starting point for a "large"
  single-VM deployment; watch resource usage under real load and scale the
  `docker-compose.yml` limits accordingly. I don't have your actual VM specs.

## Setup on your VM

1. **Copy this directory** to the VM (or clone the repo there).
2. `cp .env.example .env` and set a real `GRAFANA_ADMIN_PASSWORD`.
3. `docker compose up -d` — brings up Redpanda, ClickHouse (with schema
   auto-applied from `clickhouse/init.sql`), the classifier, and Grafana.
4. **Wire up rsyslog**: copy `rsyslog/99-kafka-forward.conf` into
   `/etc/rsyslog.d/` on the box that currently receives your syslog feed,
   adjust the `broker` address if Redpanda isn't on the same host, then
   `systemctl restart rsyslog`. Your existing LogAnalyzer pipeline is
   untouched by this.
5. Confirm data is flowing:
   ```
   docker exec -it syslog-clickhouse clickhouse-client \
     --query "SELECT count() FROM syslog_ml.events"
   ```
6. **Train the real classifier** once you have a few hours/days of traffic:
   ```
   docker exec -it syslog-clickhouse clickhouse-client --query \
     "SELECT message FROM syslog_ml.events FORMAT JSONEachRow" > logs.jsonl
   docker run --rm -v $(pwd)/ml:/app -v $(pwd)/logs.jsonl:/app/logs.jsonl \
     -v syslog-ml-analytics_model_data:/models \
     $(docker compose build -q classifier) \
     python train_classifier.py --input /app/logs.jsonl --output /models/classifier.joblib
   docker compose restart classifier
   ```
   Better: export a sample, hand-correct the `category` field for a few
   hundred rows across your device types, and pass that back in as the
   `--input` file — the script uses a `category` field when present instead
   of the weak-supervision guess.
7. Open Grafana at `http://<vm-ip>:3000` (admin / the password from `.env`)
   — the "Syslog ML" folder has the starter dashboard.

## Files

- `docker-compose.yml` — full stack.
- `rsyslog/99-kafka-forward.conf` — rsyslog snippet to mirror logs into Kafka.
- `clickhouse/init.sql` — event table + per-minute rollup.
- `ml/labeling_rules.py` — weak-supervision category rules (tune these for
  your device vendors).
- `ml/train_classifier.py` — trains the TF-IDF + linear SVM classifier.
- `ml/consumer.py` — the running pipeline (Kafka -> Drain3 -> classify -> ClickHouse).
- `grafana/` — provisioned datasource + starter dashboard.
