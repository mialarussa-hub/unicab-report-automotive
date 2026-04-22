"""Internal API for scrapers — invoked by backend or n8n workflows."""

from fastapi import FastAPI
from pydantic import BaseModel

from src.test_scrape import run_test_scrape

app = FastAPI(title="UNICAB Scrapers", docs_url="/docs")


class SourceConfig(BaseModel):
    name: str
    url: str
    source_type: str  # forum, news, youtube, social, official


class ScrapeTestRequest(BaseModel):
    brand: str
    model: str = ""
    alimentazione: str | None = None
    cilindrata: float | None = None
    sources: list[SourceConfig] = []
    session_id: str | None = None
    callback_url: str | None = None


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/scrape/test")
async def scrape_test(request: ScrapeTestRequest):
    """Run scrapers using configured sources."""
    sources_dicts = [s.model_dump() for s in request.sources]
    result = await run_test_scrape(
        request.brand, request.model, sources_dicts,
        alimentazione=request.alimentazione,
        cilindrata=request.cilindrata,
        session_id=request.session_id,
        callback_url=request.callback_url,
    )
    return result
