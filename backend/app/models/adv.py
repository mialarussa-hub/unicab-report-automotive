import uuid
from datetime import datetime

from sqlalchemy import String, Float, DateTime, Integer, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AdvSpend(Base):
    __tablename__ = "adv_spend"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    platform: Mapped[str] = mapped_column(String(100), nullable=False)  # facebook, google, youtube
    reference_month: Mapped[int] = mapped_column(Integer, index=True, nullable=False)  # YYYYMM
    estimated_spend: Mapped[float | None] = mapped_column(Float, nullable=True)
    ad_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
