from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api import auth, reports, data, sentiment, adv
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

# Frontend routes (Jinja2 templates)
app.include_router(frontend.router, prefix="/frontend", tags=["frontend"])

# Static files
static_dir = Path(__file__).parent.parent.parent / "frontend" / "static"
if static_dir.exists():
    app.mount("/frontend/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/health")
async def health():
    return {"status": "ok"}
