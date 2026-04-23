"""Frontend routes — serves Jinja2 templates for the web viewer."""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password, create_access_token, decode_access_token
from app.database import get_db
from app.models.user import User
from app.models.report import Report

router = APIRouter()

# In Docker: /app/frontend/templates (mounted volume)
# Local dev: relative path from backend/app/api/ → frontend/templates
_docker_path = Path("/app/frontend/templates")
_local_path = Path(__file__).parent.parent.parent.parent / "frontend" / "templates"
templates_dir = _docker_path if _docker_path.exists() else _local_path
templates = Jinja2Templates(directory=str(templates_dir))


async def _get_user_from_cookie(request: Request, db: AsyncSession) -> User | None:
    token = request.cookies.get("access_token")
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload:
        return None
    result = await db.execute(select(User).where(User.id == uuid.UUID(payload["sub"])))
    return result.scalar_one_or_none()


@router.get("/", response_class=HTMLResponse)
async def frontend_root(request: Request):
    return RedirectResponse(url="/frontend/login")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"error": None})


@router.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            request, "login.html", {"error": "Email o password non validi"}
        )

    token = create_access_token(data={"sub": str(user.id)})
    response = RedirectResponse(url="/frontend/dashboard", status_code=303)
    response.set_cookie(key="access_token", value=token, httponly=True)
    return response


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    user = await _get_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/frontend/login")

    reports_result = await db.execute(select(Report).order_by(Report.reference_month.desc()))
    reports = reports_result.scalars().all()

    return templates.TemplateResponse(
        request, "dashboard.html", {"user": user, "reports": reports}
    )


@router.get("/report/{report_id}", response_class=HTMLResponse)
async def view_report(request: Request, report_id: str, db: AsyncSession = Depends(get_db)):
    user = await _get_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/frontend/login")

    report_result = await db.execute(select(Report).where(Report.id == report_id))
    report = report_result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report non trovato")

    return templates.TemplateResponse(
        request, "report_viewer.html", {"user": user, "report": report}
    )


@router.get("/sources", response_class=HTMLResponse)
async def sources_page(request: Request, db: AsyncSession = Depends(get_db)):
    user = await _get_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/frontend/login")
    if not user.is_admin:
        return RedirectResponse(url="/frontend/dashboard")
    return templates.TemplateResponse(request, "sources.html", {"user": user})


@router.get("/scraping-test", response_class=HTMLResponse)
async def scraping_test_page(request: Request, db: AsyncSession = Depends(get_db)):
    user = await _get_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/frontend/login")
    if not user.is_admin:
        return RedirectResponse(url="/frontend/dashboard")
    return templates.TemplateResponse(request, "scraping_test.html", {"user": user})


@router.get("/timesheet", response_class=HTMLResponse)
async def timesheet_page(request: Request, db: AsyncSession = Depends(get_db)):
    user = await _get_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/frontend/login")
    return templates.TemplateResponse(request, "timesheet.html", {"user": user})


@router.get("/anteprime", response_class=HTMLResponse)
async def anteprime_page(request: Request, db: AsyncSession = Depends(get_db)):
    """Read-only view of featured scraping sessions. Visible to admin + client."""
    user = await _get_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/frontend/login")
    return templates.TemplateResponse(request, "anteprime.html", {"user": user})


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/frontend/login")
    response.delete_cookie("access_token")
    return response
