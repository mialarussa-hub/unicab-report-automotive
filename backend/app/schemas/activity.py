"""Pydantic schemas for timesheet activities."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class ActivityCreate(BaseModel):
    activity_date: date
    description: str = Field(..., max_length=500)
    hours: float = Field(..., gt=0, le=24)
    category: str
    notes: str | None = None


class ActivityUpdate(BaseModel):
    activity_date: date | None = None
    description: str | None = Field(None, max_length=500)
    hours: float | None = Field(None, gt=0, le=24)
    category: str | None = None
    notes: str | None = None


class ActivityRead(BaseModel):
    id: uuid.UUID
    activity_date: date
    description: str
    hours: float
    category: str
    notes: str | None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MonthlySummary(BaseModel):
    month: str
    total_hours: float
    by_category: dict[str, float]
    activity_count: int
