from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.sentiment import SentimentScore
from app.models.user import User
from app.schemas.sentiment import SentimentScoreRead

router = APIRouter()


@router.get("/", response_model=list[SentimentScoreRead])
async def list_sentiment(
    brand: str | None = Query(None),
    reference_month: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(SentimentScore)
    if brand:
        query = query.where(SentimentScore.brand == brand)
    if reference_month:
        query = query.where(SentimentScore.reference_month == reference_month)

    result = await db.execute(query.order_by(SentimentScore.collected_at.desc()))
    return result.scalars().all()
