from pydantic import BaseModel


class LogAssistantQuery(BaseModel):
    question: str


class LogMatch(BaseModel):
    event_time: str
    hostname: str
    severity: str
    program: str
    message: str
    predicted_category: str
    is_anomaly: bool
    score: float


class SemanticSearchResponse(BaseModel):
    items: list[LogMatch]


class AskResponse(BaseModel):
    answer: str
    sources: list[LogMatch]
