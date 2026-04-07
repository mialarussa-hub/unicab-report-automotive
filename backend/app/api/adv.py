from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.adv import AdvSpend
from app.models.user import User
from app.schemas.adv import AdvSpendRead

router = APIRouter()


@router.get("/", response_model=list[AdvSpendRead])
async def list_adv_spend(
    brand: str | None = Query(None),
    reference_month: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(AdvSpend)
    if brand:
        query = query.where(AdvSpend.brand == brand)
    if reference_month:
        query = query.where(AdvSpend.reference_month == reference_month)

    result = await db.execute(query.order_by(AdvSpend.collected_at.desc()))
    return result.scalars().all()
