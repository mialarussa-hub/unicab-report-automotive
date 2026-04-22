"""CRUD endpoints for scraping sources."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.scraping_test import get_admin_from_cookie
from app.database import get_db
from app.models.source import Source
from app.models.user import User
from app.schemas.source import SourceCreate, SourceRead

router = APIRouter()


@router.get("/", response_model=list[SourceRead])
async def list_sources(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_from_cookie),
):
    result = await db.execute(select(Source).order_by(Source.name))
    return result.scalars().all()


@router.post("/", response_model=SourceRead, status_code=201)
async def create_source(
    source_in: SourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_from_cookie),
):
    source = Source(
        name=source_in.name,
        url=source_in.url,
        source_type=source_in.source_type,
    )
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return source


@router.delete("/{source_id}", status_code=204)
async def delete_source(
    source_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_from_cookie),
):
    result = await db.execute(select(Source).where(Source.id == uuid.UUID(source_id)))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    await db.delete(source)
    await db.commit()


@router.patch("/{source_id}/toggle", response_model=SourceRead)
async def toggle_source(
    source_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_from_cookie),
):
    result = await db.execute(select(Source).where(Source.id == uuid.UUID(source_id)))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    source.is_active = not source.is_active
    await db.commit()
    await db.refresh(source)
    return source
