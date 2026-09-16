"""
Device identity resolution: source IP -> hostname / vendor / model.

Since SNMP credentials aren't centrally tracked yet, this never guesses a
community string. It only attempts SNMP for an IP that has a matching row
in snmp_credentials.csv (exact IP or CIDR match). Everything else falls
back to the hostname the device itself put in the syslog message, or
finally the bare source IP — always with `resolution_method` recorded so
you can see exactly how confident each row's identity is (and which
devices still need a credential added).

Uses the net-snmp CLI (`snmpget`) via subprocess rather than a Python SNMP
library: it's what `apt install snmp` gives you natively on Ubuntu/Debian,
handles v1/v2c/v3 uniformly, and one subprocess call per OID is plenty fast
for periodic (not per-message) resolution.
"""
import csv
import ipaddress
import logging
import subprocess

log = logging.getLogger("device_resolver")

SYS_NAME_OID = "1.3.6.1.2.1.1.5.0"
SYS_DESCR_OID = "1.3.6.1.2.1.1.1.0"
SYS_OBJECT_ID_OID = "1.3.6.1.2.1.1.2.0"

# Well-known IANA private enterprise numbers (iana.org/assignments/enterprise-numbers).
# Not exhaustive — extend this as you encounter vendors it doesn't recognize;
# unmatched OIDs fall back to vendor="unknown" rather than a guess.
VENDOR_OID_PREFIXES = {
    "1.3.6.1.4.1.9.": "cisco",
    "1.3.6.1.4.1.2636.": "juniper",
    "1.3.6.1.4.1.12356.": "fortinet",
    "1.3.6.1.4.1.2011.": "huawei",
    "1.3.6.1.4.1.25461.": "paloalto",
    "1.3.6.1.4.1.30065.": "arista",
    "1.3.6.1.4.1.14988.": "mikrotik",
    "1.3.6.1.4.1.11.": "hp",
    "1.3.6.1.4.1.14823.": "aruba",
    "1.3.6.1.4.1.674.": "dell",
    "1.3.6.1.4.1.41112.": "ubiquiti",
    "1.3.6.1.4.1.8072.": "net-snmp",  # generic Linux/Unix hosts running net-snmp
}

SNMP_TIMEOUT_SECONDS = 3
SNMP_RETRIES = 1


class Credential:
    def __init__(self, row):
        self.network = ipaddress.ip_network(row["ip_or_cidr"], strict=False)
        self.version = row["version"].strip().lower()
        self.community = row.get("community", "").strip()
        self.v3_user = row.get("v3_user", "").strip()
        self.v3_level = row.get("v3_level", "authPriv").strip()
        self.v3_auth_proto = row.get("v3_auth_proto", "SHA").strip()
        self.v3_auth_pass = row.get("v3_auth_pass", "").strip()
        self.v3_priv_proto = row.get("v3_priv_proto", "AES").strip()
        self.v3_priv_pass = row.get("v3_priv_pass", "").strip()

    def contains(self, ip):
        try:
            return ipaddress.ip_address(ip) in self.network
        except ValueError:
            return False

    def snmpget_args(self):
        if self.version == "v3":
            return [
                "-v3", "-u", self.v3_user, "-l", self.v3_level,
                "-a", self.v3_auth_proto, "-A", self.v3_auth_pass,
                "-x", self.v3_priv_proto, "-X", self.v3_priv_pass,
            ]
        return ["-v", self.version, "-c", self.community]


def load_credentials(path):
    """Returns a list of Credential objects, most-specific network first."""
    credentials = []
    try:
        with open(path, newline="") as f:
            for row in csv.DictReader(f):
                ip_or_cidr = (row.get("ip_or_cidr") or "").strip()
                if not ip_or_cidr or ip_or_cidr.startswith("#"):
                    continue
                try:
                    credentials.append(Credential(row))
                except (KeyError, ValueError) as exc:
                    log.warning("Skipping malformed credential row %r: %s", row, exc)
    except FileNotFoundError:
        log.warning("No credentials file at %s — SNMP resolution disabled until it exists", path)
        return []
    # Prefer exact /32 host entries over broader subnets when both match.
    credentials.sort(key=lambda c: c.network.num_addresses)
    return credentials


def find_credential(credentials, ip):
    for cred in credentials:
        if cred.contains(ip):
            return cred
    return None


def _snmpget(ip, oid, credential):
    cmd = ["snmpget", "-O", "qv", "-t", str(SNMP_TIMEOUT_SECONDS), "-r", str(SNMP_RETRIES)]
    cmd += credential.snmpget_args()
    cmd += [ip, oid]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=SNMP_TIMEOUT_SECONDS * (SNMP_RETRIES + 2))
    except subprocess.TimeoutExpired:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip().strip('"')


def vendor_from_object_id(object_id):
    if not object_id:
        return "unknown"
    for prefix, vendor in VENDOR_OID_PREFIXES.items():
        if object_id.startswith(prefix):
            return vendor
    return "unknown"


def resolve_via_snmp(ip, credential):
    """Returns (hostname, vendor, model) or None if SNMP didn't respond."""
    sys_name = _snmpget(ip, SYS_NAME_OID, credential)
    if sys_name is None:
        return None
    sys_descr = _snmpget(ip, SYS_DESCR_OID, credential) or ""
    sys_object_id = _snmpget(ip, SYS_OBJECT_ID_OID, credential) or ""
    vendor = vendor_from_object_id(sys_object_id)
    model = sys_descr[:200]
    return sys_name or ip, vendor, model
