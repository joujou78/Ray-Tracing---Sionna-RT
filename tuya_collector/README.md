# Tuya Circuit Breaker Collector

Polls Tuya circuit breakers directly over local LAN and writes to InfluxDB.
Runs in parallel with Home Assistant — does not interfere with existing pipeline.

## Requirements

```bash
pip3 install tinytuya influxdb-client pyaes
```

## Setup

### 1. Create directories
```bash
mkdir -p /opt/tuya_collector /etc/tuya
```

### 2. Deploy script
```bash
cp tuya_collector.py /opt/tuya_collector/
```

### 3. Create /etc/tuya/devices.json
See `devices.example.json` for format. Each device needs `name`, `id`, `key`, and `ip`.

Find live device IPs by scanning:
```bash
nmap -p 6668 10.0.11.0/24 10.5.240.0/24 --open
```

Get device IDs and keys by running:
```bash
python3 -m tinytuya wizard
```

### 4. Deploy systemd service
```bash
cp tuya-collector.service /etc/systemd/system/
# Edit INFLUX_TOKEN in the service file
systemctl daemon-reload
systemctl enable tuya-collector
systemctl start tuya-collector
```

### 5. Verify
```bash
journalctl -u tuya-collector -f
```

## DP Mapping

| DP | Measurement | Scale | Unit |
|----|-------------|-------|------|
| 17 | total_energy | /1000 | kWh |
| 18 | current | /1000 | A |
| 19 | power | /10 | W |
| 20 | voltage | /10 | V |

## InfluxDB tags

Entity IDs follow Home Assistant naming: `circuit_breaker_<name>_<suffix>`
so existing Grafana dashboards work without changes.
