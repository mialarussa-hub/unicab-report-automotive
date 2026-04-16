from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api import auth, reports, data, sentiment, adv, scraping_test, sources, timesheet
from app.api import frontend

app = FastAPI(
    title="UNICAB Report Automotive",
    description="API per il sistema di report automotive data-driven UNICAB",
    version="0.1.0",
)

# API routes
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(reports.router, prefix="/reports", tags=["reports"])
app.include_router(data.router, prefix="/data", tags=["data"])
app.include_router(sentiment.router, prefix="/sentiment", tags=["sentiment"])
app.include_router(adv.router, prefix="/adv", tags=["adv"])
app.include_router(scraping_test.router, prefix="/scraping-test", tags=["scraping-test"])
app.include_router(sources.router, prefix="/sources", tags=["sources"])
app.include_router(timesheet.router, prefix="/timesheet", tags=["timesheet"])

# Frontend routes (Jinja2 templates)
app.include_router(frontend.router, prefix="/frontend", tags=["frontend"])

# Static files
_docker_static = Path("/app/frontend/static")
_local_static = Path(__file__).parent.parent.parent / "frontend" / "static"
static_dir = _docker_static if _docker_static.exists() else _local_static
if static_dir.exists():
    app.mount("/frontend/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def root():
    """Redirect root to frontend login page."""
    return RedirectResponse(url="/frontend/login")


@app.get("/health")
async def health():
    return {"status": "ok"}
