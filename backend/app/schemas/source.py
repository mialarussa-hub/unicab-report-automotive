import uuid
from datetime import datetime

from pydantic import BaseModel


class SourceCreate(BaseModel):
    name: str
    url: str
    source_type: str  # forum, news, youtube, social


class SourceRead(BaseModel):
    id: uuid.UUID
    name: str
    url: str
    source_type: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
