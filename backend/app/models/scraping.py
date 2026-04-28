"""Scraping session and result models for persisting scraping data."""

import uuid
from datetime import datetime

from sqlalchemy import String, Text, Integer, Float, DateTime, ForeignKey, func, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ScrapingSession(Base):
    __tablename__ = "scraping_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="running")  # running, completed, failed
    total_sources: Mapped[int] = mapped_column(Integer, default=0)
    total_results: Mapped[int] = mapped_column(Integer, default=0)
    total_comments: Mapped[int] = mapped_column(Integer, default=0)
    total_credits: Mapped[int] = mapped_column(Integer, default=0)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    # Riepilogo per-fonte: lista di dict con {source, source_type, status, result_count,
    # credits_used, duration_ms, error}. Permette di mostrare nella UI anche le fonti
    # interrogate ma senza risultati (status=partial/error).
    source_runs: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    # Minireport L2: sintesi narrativa dei media/giornalisti per il modello — tono
    # commenti utenti + punti di forza/debolezza ricorrenti. Generato via Claude
    # alla fine della sessione, una sola chiamata aggregata su tutti gli articoli L2.
    l2_synthesis: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    phase_filter: Mapped[str] = mapped_column(String(10), default="all", nullable=False)  # all, L1, L2, L3
    filter_alimentazione: Mapped[str | None] = mapped_column(String(30), nullable=True)
    filter_cilindrata: Mapped[float | None] = mapped_column(Numeric(3, 1), nullable=True)
    filter_effective: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    # Flag: mark this session as "anteprima" visible to all authenticated users
    # (admin + client) on the dashboard Anteprime tab. Toggled only by admin.
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    results: Mapped[list["ScrapingResult"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", lazy="selectin"
    )


class ScrapingResult(Base):
    __tablename__ = "scraping_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scraping_sessions.id", ondelete="CASCADE"),
        index=True, nullable=False
    )
    source_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)  # forum, news, youtube, official
    url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_comments: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    comment_count: Mapped[int] = mapped_column(Integer, default=0)
    view_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    like_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    channel: Mapped[str | None] = mapped_column(String(255), nullable=True)
    official_info: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # L1: structured brand communication data
    motore_info: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # {versioni: [{alimentazione, cilindrata, descrizione}]}
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session: Mapped["ScrapingSession"] = relationship(back_populates="results")
