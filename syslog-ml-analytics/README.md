# Syslog ML Analytics (native install, Ubuntu/Debian)

A syslog analytics stack with its own database and ML classification layer,
installed directly on your VM (no Docker), sitting **alongside** your
existing rsyslog/syslog-ng + LogAnalyzer setup — that pipeline is untouched.

## Architecture

```
network devices --syslog--> rsyslog (existing) ----------> LogAnalyzer DB (unchanged)
                                  |
                                  +--omfile (JSON copy)--> /var/log/syslog-ml/raw.jsonl
                                                                   |
                                                     syslog-ml-classifier.service (tails file)
                                                     - device identity lookup (cached)
                                                     - Drain3 template mining
                                                     - ML category classifier
                                                                   |
                                                              ClickHouse
                                                                   |
                                                                Grafana

                          (separate, async, every 10 min)
          syslog-ml-resolver.timer -> resolve_pending.py
             for each IP seen but not yet identified:
               - has a credential in snmp_credentials.csv? -> SNMP sysName/sysDescr/sysObjectID
               - writes result into ClickHouse device_inventory
```

No message broker: one VM, one rsyslog instance receiving everything, so a
locally tailed file is enough durability without adding a Kafka/Redpanda
service to operate.

## Why this design, and what it deliberately doesn't do

- **No SNMP credential guessing.** Since communities aren't centrally
  tracked, the resolver only ever attempts SNMP for an IP that has a row in
  `ml/snmp_credentials.csv` — never a default/common-string guess. Add rows
  as you onboard devices; everything else keeps working in the meantime.
- **Identity has three tiers, always labeled:** `resolution_method` on every
  event is `snmp` (verified via sysName), `syslog_reported` (the device's
  own hostname claim, unverified), or `unresolved` (source IP only). The
  Grafana dashboard's "Device identity resolution" panel shows the split so
  you can see the onboarding backlog shrink over time — nothing pretends to
  know a hostname it doesn't.
- **Classification is TF-IDF + linear SVM on Drain3-mined templates**, not a
  transformer. It's the right cost/accuracy trade-off for CPU-only, 10M+
  lines/day; see the "algorithm" note in `ml/train_classifier.py`'s
  docstring for the reasoning.
- **No labeled training data exists yet.** `ml/labeling_rules.py`'s
  keyword rules bootstrap categories until you train on reviewed labels.
  Treat early `predicted_category` values as a rough sort, not verified
  fact — especially for vendor-specific message formats the generic rules
  don't cover yet.
- Sizing/timing constants (10-minute resolver interval, 60s inventory cache
  refresh, etc.) are reasonable starting points, not measured against your
  actual traffic — watch resource usage and adjust.

## Step 1 — create the service account and directories

```bash
sudo groupadd --system syslog-ml
sudo useradd --system --gid syslog-ml --home /opt/syslog-ml --shell /usr/sbin/nologin syslog-ml

sudo mkdir -p /opt/syslog-ml /etc/syslog-ml /var/lib/syslog-ml
sudo mkdir -p -m 2750 /var/log/syslog-ml   # setgid so files rsyslog creates inherit this group
sudo chown syslog-ml:syslog-ml /var/lib/syslog-ml
sudo chown root:syslog-ml /var/log/syslog-ml /etc/syslog-ml
```

## Step 2 — install ClickHouse (official repo)

```bash
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg
curl -fsSL 'https://packages.clickhouse.com/rpm/lts/repodata/repomd.xml.key' | sudo gpg --dearmor -o /usr/share/keyrings/clickhouse-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/clickhouse-keyring.gpg] https://packages.clickhouse.com/deb stable main" | sudo tee /etc/apt/sources.list.d/clickhouse.list
sudo apt-get update
sudo apt-get install -y clickhouse-server clickhouse-client
sudo systemctl enable --now clickhouse-server
```

Apply the schema:

```bash
sudo cp clickhouse/init.sql /tmp/init.sql
clickhouse-client --multiquery < /tmp/init.sql
clickhouse-client --query "SHOW TABLES FROM syslog_ml"
```

**Checkpoint** — confirm `device_inventory` and `events` are listed before continuing.

## Step 3 — install Grafana (official repo)

```bash
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://apt.grafana.com/gpg.key | sudo gpg --dearmor -o /etc/apt/keyrings/grafana.gpg
echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com stable main" | sudo tee /etc/apt/sources.list.d/grafana.list
sudo apt-get update
sudo apt-get install -y grafana
sudo grafana-cli plugins install grafana-clickhouse-datasource
sudo systemctl enable --now grafana-server
```

Provision the datasource and dashboard:

```bash
sudo cp grafana/provisioning/datasources/clickhouse.yaml /etc/grafana/provisioning/datasources/
sudo cp grafana/provisioning/dashboards/dashboard.yaml /etc/grafana/provisioning/dashboards/
sudo mkdir -p /var/lib/grafana/dashboards
sudo cp grafana/dashboards/syslog_ml_overview.json /var/lib/grafana/dashboards/
sudo systemctl restart grafana-server
```

**Checkpoint** — open `http://<vm-ip>:3000` (default admin/admin, change it), confirm the ClickHouse datasource connects and the "Syslog ML" dashboard folder appears (panels will be empty until Step 5).

## Step 4 — install the Python pipeline

```bash
sudo apt-get install -y python3-venv snmp snmp-mibs-downloader
sudo cp -r ml /opt/syslog-ml/ml
sudo python3 -m venv /opt/syslog-ml/venv
sudo /opt/syslog-ml/venv/bin/pip install -r /opt/syslog-ml/ml/requirements.txt
sudo cp ml/snmp_credentials.csv.example /etc/syslog-ml/snmp_credentials.csv
sudo chown syslog-ml:syslog-ml /opt/syslog-ml/ml/*.py
```

Edit `/etc/syslog-ml/snmp_credentials.csv` and add entries as you have them
(see the comments in the file) — it's fine to leave it empty for now.

## Step 5 — wire up rsyslog and the systemd services

```bash
sudo cp rsyslog/60-syslog-ml.conf /etc/rsyslog.d/
sudo systemctl restart rsyslog

sudo cp systemd/syslog-ml-classifier.service systemd/syslog-ml-resolver.service systemd/syslog-ml-resolver.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now syslog-ml-classifier.service
sudo systemctl enable --now syslog-ml-resolver.timer
```

**Checkpoint:**

```bash
sudo tail -f /var/log/syslog-ml/raw.jsonl              # confirm rsyslog is writing
sudo journalctl -u syslog-ml-classifier -f              # confirm it's processing
clickhouse-client --query "SELECT count() FROM syslog_ml.events"
```

## Step 6 — train the real classifier (after a few hours/days of traffic)

```bash
clickhouse-client --query "SELECT message FROM syslog_ml.events FORMAT JSONEachRow" > /tmp/logs.jsonl
sudo -u syslog-ml /opt/syslog-ml/venv/bin/python /opt/syslog-ml/ml/train_classifier.py \
  --input /tmp/logs.jsonl --output /var/lib/syslog-ml/classifier.joblib
sudo systemctl restart syslog-ml-classifier
```

Better: export a sample, hand-correct the `category` field for a few hundred
rows across your different vendors, and re-run with that file — the script
prefers a real `category` field over the weak-supervision guess.

## Files

- `clickhouse/init.sql` — `device_inventory`, `events`, and the per-minute rollup.
- `rsyslog/60-syslog-ml.conf` — mirrors rsyslog's feed to a local JSON file.
- `ml/consumer.py` — tails the file, resolves identity, classifies, writes to ClickHouse.
- `ml/device_resolver.py` / `ml/resolve_pending.py` — the opt-in SNMP identity resolver.
- `ml/snmp_credentials.csv.example` — per-device/subnet SNMP credentials (copy, fill in incrementally).
- `ml/labeling_rules.py` — weak-supervision category rules (tune for your vendors).
- `ml/train_classifier.py` — trains the TF-IDF + linear SVM classifier.
- `systemd/` — unit files for the classifier and the resolver timer.
- `grafana/` — provisioned datasource + starter dashboard.
