from datetime import datetime

from pydantic import BaseModel


class LogEventRead(BaseModel):
    event_time: datetime
    received_at: datetime
    source_ip: str
    hostname: str
    vendor: str
    model: str
    resolution_method: str
    facility: str
    severity: str
    severity_num: int
    program: str
    pid: int | None
    message: str
    predicted_category: str
    predicted_confidence: float
    is_anomaly: bool


class LogSearchResponse(BaseModel):
    items: list[LogEventRead]
    total: int
    page: int
    page_size: int
