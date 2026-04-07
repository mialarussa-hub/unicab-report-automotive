"""Internal API for scrapers — invoked by backend or n8n workflows."""

from fastapi import FastAPI
from pydantic import BaseModel

from src.test_scrape import run_test_scrape

app = FastAPI(title="UNICAB Scrapers", docs_url="/docs")


class ScrapeTestRequest(BaseModel):
    brand: str
    model: str = ""


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/scrape/test")
async def scrape_test(request: ScrapeTestRequest):
    """Run all scrapers in parallel and return aggregated results."""
    result = await run_test_scrape(request.brand, request.model)
    return result


@app.post("/scrape/forums")
async def scrape_forums_endpoint(brand: str = "", model: str = ""):
    """Trigger forum scraping for a specific brand."""
    from src.forums import scrape_forums
    from dataclasses import asdict
    result = await scrape_forums(brand, model)
    return asdict(result)


@app.post("/scrape/youtube")
async def scrape_youtube_endpoint(brand: str = "", model: str = ""):
    """Trigger YouTube sentiment collection."""
    from src.youtube import scrape_youtube
    from dataclasses import asdict
    result = await scrape_youtube(brand, model)
    return asdict(result)
