from datetime import datetime, timedelta, timezone

from clickhouse_connect.driver.client import Client

from app.schemas.log_event import LogEventRead, LogSearchResponse

_EVENT_COLUMNS = [
    "event_time", "received_at", "source_ip", "hostname", "vendor", "model",
    "resolution_method", "facility", "severity", "severity_num", "program",
    "pid", "message", "predicted_category", "predicted_confidence", "is_anomaly",
]

# Matches events' own TTL (see clickhouse/init.sql) -- nothing older than
# this exists to search for anyway.
MAX_HOURS = 24 * 90
MAX_PAGE_SIZE = 500


def _build_where(
    *,
    hours: int,
    source_ip: str | None,
    hostname: str | None,
    severity: str | None,
    program: str | None,
    predicted_category: str | None,
    is_anomaly: bool | None,
    q: str | None,
) -> tuple[str, dict]:
    """Every filter is bound as a query parameter, never interpolated into
    the SQL string -- q/hostname/program come straight from the caller."""
    conditions = ["event_time >= %(since)s"]
    params: dict = {"since": datetime.now(timezone.utc) - timedelta(hours=hours)}

    if source_ip:
        conditions.append("source_ip = %(source_ip)s")
        params["source_ip"] = source_ip
    if hostname:
        conditions.append("positionCaseInsensitive(hostname, %(hostname)s) > 0")
        params["hostname"] = hostname
    if severity:
        conditions.append("severity = %(severity)s")
        params["severity"] = severity
    if program:
        conditions.append("positionCaseInsensitive(program, %(program)s) > 0")
        params["program"] = program
    if predicted_category:
        conditions.append("predicted_category = %(predicted_category)s")
        params["predicted_category"] = predicted_category
    if is_anomaly is not None:
        conditions.append("is_anomaly = %(is_anomaly)s")
        params["is_anomaly"] = 1 if is_anomaly else 0
    if q:
        conditions.append("positionCaseInsensitive(message, %(q)s) > 0")
        params["q"] = q

    return " AND ".join(conditions), params


def search_events(
    client: Client,
    *,
    hours: int = 24,
    source_ip: str | None = None,
    hostname: str | None = None,
    severity: str | None = None,
    program: str | None = None,
    predicted_category: str | None = None,
    is_anomaly: bool | None = None,
    q: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> LogSearchResponse:
    hours = max(1, min(hours, MAX_HOURS))
    page = max(1, page)
    page_size = max(1, min(page_size, MAX_PAGE_SIZE))

    where_clause, params = _build_where(
        hours=hours,
        source_ip=source_ip,
        hostname=hostname,
        severity=severity,
        program=program,
        predicted_category=predicted_category,
        is_anomaly=is_anomaly,
        q=q,
    )

    total = client.query(
        f"SELECT count() FROM syslog_ml.events WHERE {where_clause}",
        parameters=params,
    ).result_rows[0][0]

    page_params = {**params, "limit": page_size, "offset": (page - 1) * page_size}
    rows_query = f"""
        SELECT {', '.join(_EVENT_COLUMNS)}
        FROM syslog_ml.events
        WHERE {where_clause}
        ORDER BY event_time DESC
        LIMIT %(limit)s OFFSET %(offset)s
    """
    result = client.query(rows_query, parameters=page_params)
    items = [LogEventRead(**dict(zip(_EVENT_COLUMNS, row))) for row in result.result_rows]

    return LogSearchResponse(items=items, total=total, page=page, page_size=page_size)
