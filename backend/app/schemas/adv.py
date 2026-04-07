import uuid
from datetime import datetime

from pydantic import BaseModel


class AdvSpendRead(BaseModel):
    id: uuid.UUID
    brand: str
    platform: str
    reference_month: int
    estimated_spend: float | None = None
    ad_count: int | None = None
    collected_at: datetime

    model_config = {"from_attributes": True}
