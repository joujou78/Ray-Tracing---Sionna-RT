#!/usr/bin/env python3
import json, logging, os, sys, time
import tinytuya
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

INFLUX_URL    = os.getenv("INFLUX_URL",    "http://localhost:8086")
INFLUX_TOKEN  = os.getenv("INFLUX_TOKEN",  "REPLACE_WITH_TOKEN")
INFLUX_ORG    = os.getenv("INFLUX_ORG",    "grafana")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "energy")
DEVICES_FILE  = os.getenv("DEVICES_FILE",  "/etc/tuya/devices.json")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "30"))
TUYA_VERSION  = float(os.getenv("TUYA_VERSION", "3.4"))

DP_MAP = {
    "17": ("kWh", 1000.0, "total_energy"),
    "18": ("A",   1000.0, "current"),
    "19": ("W",   10.0,   "power"),
    "20": ("V",   10.0,   "voltage"),
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", stream=sys.stdout)
log = logging.getLogger("tuya_collector")


def load_devices(path):
    with open(path) as f:
        raw = json.load(f)
    return raw if isinstance(raw, list) else raw.get("devices", [])


def build_device(dev):
    dev_id  = dev.get("id") or dev.get("devId")
    dev_key = dev.get("key") or dev.get("localKey")
    dev_ip  = dev.get("ip")
    name    = dev.get("name", dev_id)
    if not (dev_id and dev_key and dev_ip):
        log.debug("Skipping %s — missing id/key/ip", name)
        return None
    d = tinytuya.OutletDevice(dev_id, dev_ip, dev_key)
    d.set_version(TUYA_VERSION)
    d.set_socketTimeout(5)
    d.name = name
    return d


def sanitise_name(name):
    return name.lower().replace(" ", "_").replace("-", "_")


def poll_device(d):
    try:
        status = d.status()
        if status and "dps" in status:
            return status["dps"]
        log.warning("%s: unexpected response %s", d.name, status)
    except Exception as e:
        log.warning("%s: poll error — %s", d.name, e)
    return None


def write_points(write_api, bucket, org, base_name, dps):
    points = []
    for dp_str, (meas, scale, suffix) in DP_MAP.items():
        raw = dps.get(dp_str) or dps.get(int(dp_str))
        if raw is None:
            continue
        try:
            value = float(raw) / scale
        except (TypeError, ValueError):
            continue
        entity_id = f"circuit_breaker_{base_name}_{suffix}"
        p = (Point(meas).tag("entity_id", entity_id).field("value", value)
             .time(int(time.time()), WritePrecision.SECONDS))
        points.append(p)
    if points:
        write_api.write(bucket=bucket, org=org, record=points)
        log.debug("%s: wrote %d points", base_name, len(points))


def main():
    if not os.path.exists(DEVICES_FILE):
        log.error("Devices file not found: %s", DEVICES_FILE)
        sys.exit(1)
    devices = [d for d in (build_device(r) for r in load_devices(DEVICES_FILE)) if d]
    log.info("Loaded %d devices with IPs", len(devices))
    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    write_api = client.write_api(write_options=SYNCHRONOUS)
    log.info("Polling every %ds", POLL_INTERVAL)
    while True:
        for dev in devices:
            dps = poll_device(dev)
            if dps:
                write_points(write_api, INFLUX_BUCKET, INFLUX_ORG, sanitise_name(dev.name), dps)
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
