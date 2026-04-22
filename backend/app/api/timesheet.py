"""CRUD endpoints for timesheet activities."""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import PlainTextResponse
from sqlalchemy import select, extract, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.scraping_test import get_admin_from_cookie
from app.database import get_db
from app.models.activity import Activity
from app.models.user import User
from app.schemas.activity import ActivityCreate, ActivityUpdate, ActivityRead, MonthlySummary

router = APIRouter()

ALLOWED_CATEGORIES = ["development", "research", "meeting", "documentation", "deployment"]

CATEGORY_LABELS = {
    "development": "Sviluppo",
    "research": "Ricerca",
    "meeting": "Riunione",
    "documentation": "Documentazione",
    "deployment": "Deploy",
}


def _parse_month(month: str | None) -> tuple[int, int] | None:
    """Parse 'YYYY-MM' string into (year, month) or None."""
    if not month:
        return None
    try:
        parts = month.split("-")
        return int(parts[0]), int(parts[1])
    except (ValueError, IndexError):
        return None


@router.get("/summary", response_model=MonthlySummary)
async def monthly_summary(
    month: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_from_cookie),
):
    parsed = _parse_month(month)
    if not parsed:
        raise HTTPException(status_code=400, detail="Formato mese non valido (YYYY-MM)")
    year, mo = parsed

    base_filter = [
        Activity.created_by == current_user.id,
        extract("year", Activity.activity_date) == year,
        extract("month", Activity.activity_date) == mo,
    ]

    # Total hours and count
    totals = await db.execute(
        select(func.coalesce(func.sum(Activity.hours), 0), func.count(Activity.id))
        .where(*base_filter)
    )
    total_hours, activity_count = totals.one()

    # Hours by category
    cat_rows = await db.execute(
        select(Activity.category, func.sum(Activity.hours))
        .where(*base_filter)
        .group_by(Activity.category)
    )
    by_category = {row[0]: round(row[1], 2) for row in cat_rows.all()}

    return MonthlySummary(
        month=month,
        total_hours=round(float(total_hours), 2),
        by_category=by_category,
        activity_count=activity_count,
    )


@router.get("/export")
async def export_month(
    month: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_from_cookie),
):
    parsed = _parse_month(month)
    if not parsed:
        raise HTTPException(status_code=400, detail="Formato mese non valido")
    year, mo = parsed

    result = await db.execute(
        select(Activity)
        .where(
            Activity.created_by == current_user.id,
            extract("year", Activity.activity_date) == year,
            extract("month", Activity.activity_date) == mo,
        )
        .order_by(Activity.activity_date)
    )
    activities = result.scalars().all()

    # Build text report
    lines = [
        f"REPORT ATTIVITA - {month}",
        f"{'=' * 40}",
        f"Operatore: {current_user.full_name}",
        "",
    ]

    total = 0.0
    cat_totals: dict[str, float] = {}
    for a in activities:
        label = CATEGORY_LABELS.get(a.category, a.category)
        lines.append(f"{a.activity_date.strftime('%d/%m/%Y')}  [{label}]  {a.hours}h")
        lines.append(f"  {a.description}")
        if a.notes:
            lines.append(f"  Note: {a.notes}")
        lines.append("")
        total += a.hours
        cat_totals[label] = cat_totals.get(label, 0) + a.hours

    lines.append(f"{'=' * 40}")
    lines.append(f"TOTALE ORE: {round(total, 2)}h")
    lines.append("")
    lines.append("Riepilogo per categoria:")
    for cat, h in sorted(cat_totals.items()):
        lines.append(f"  {cat}: {round(h, 2)}h")

    return PlainTextResponse(
        content="\n".join(lines),
        headers={"Content-Disposition": f'attachment; filename="report_{month}.txt"'},
    )


@router.get("/", response_model=list[ActivityRead])
async def list_activities(
    month: str | None = Query(None, pattern=r"^\d{4}-\d{2}$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_from_cookie),
):
    stmt = select(Activity).where(Activity.created_by == current_user.id)

    parsed = _parse_month(month)
    if parsed:
        year, mo = parsed
        stmt = stmt.where(
            extract("year", Activity.activity_date) == year,
            extract("month", Activity.activity_date) == mo,
        )

    stmt = stmt.order_by(Activity.activity_date.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=ActivityRead, status_code=201)
async def create_activity(
    data: ActivityCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_from_cookie),
):
    if data.category not in ALLOWED_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Categoria non valida. Valori ammessi: {', '.join(ALLOWED_CATEGORIES)}",
        )

    activity = Activity(
        activity_date=data.activity_date,
        description=data.description,
        hours=data.hours,
        category=data.category,
        notes=data.notes,
        created_by=current_user.id,
    )
    db.add(activity)
    await db.commit()
    await db.refresh(activity)
    return activity


@router.put("/{activity_id}", response_model=ActivityRead)
async def update_activity(
    activity_id: str,
    data: ActivityUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_from_cookie),
):
    result = await db.execute(
        select(Activity).where(
            Activity.id == uuid.UUID(activity_id),
            Activity.created_by == current_user.id,
        )
    )
    activity = result.scalar_one_or_none()
    if not activity:
        raise HTTPException(status_code=404, detail="Attivita non trovata")

    update_data = data.model_dump(exclude_unset=True)
    if "category" in update_data and update_data["category"] not in ALLOWED_CATEGORIES:
        raise HTTPException(status_code=400, detail="Categoria non valida")

    for field, value in update_data.items():
        setattr(activity, field, value)

    await db.commit()
    await db.refresh(activity)
    return activity


@router.delete("/{activity_id}", status_code=204)
async def delete_activity(
    activity_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_from_cookie),
):
    result = await db.execute(
        select(Activity).where(
            Activity.id == uuid.UUID(activity_id),
            Activity.created_by == current_user.id,
        )
    )
    activity = result.scalar_one_or_none()
    if not activity:
        raise HTTPException(status_code=404, detail="Attivita non trovata")
    await db.delete(activity)
    await db.commit()
