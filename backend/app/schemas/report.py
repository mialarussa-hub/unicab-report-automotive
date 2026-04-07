import uuid
from datetime import datetime

from pydantic import BaseModel


class ReportCreate(BaseModel):
    title: str
    reference_month: int


class ReportRead(BaseModel):
    id: uuid.UUID
    title: str
    reference_month: int
    status: str
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None = None

    model_config = {"from_attributes": True}


class ReportDetail(ReportRead):
    content_draft: str | None = None
    content_final: str | None = None
    metadata_json: dict | None = None
