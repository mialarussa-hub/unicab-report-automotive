import uuid
from datetime import datetime

from pydantic import BaseModel


class SentimentScoreRead(BaseModel):
    id: uuid.UUID
    brand: str
    model: str | None = None
    source: str
    reference_month: int
    score: float
    topic: str | None = None
    summary: str | None = None
    collected_at: datetime

    model_config = {"from_attributes": True}
