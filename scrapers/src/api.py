"""Internal API for scrapers — invoked by n8n workflows."""

from fastapi import FastAPI

app = FastAPI(title="UNICAB Scrapers", docs_url="/docs")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/scrape/forums")
async def scrape_forums(brand: str | None = None):
    """Trigger forum scraping for a specific brand or all brands."""
    # TODO: implement in AI layer sprint
    return {"status": "not_implemented", "message": "Forum scraping — to be implemented"}


@app.post("/scrape/youtube")
async def scrape_youtube(brand: str | None = None):
    """Trigger YouTube sentiment collection."""
    # TODO: implement
    return {"status": "not_implemented"}


@app.post("/scrape/facebook-ads")
async def scrape_facebook_ads(brand: str | None = None):
    """Trigger Facebook Ads Library data collection."""
    # TODO: implement
    return {"status": "not_implemented"}


@app.post("/scrape/google-ads")
async def scrape_google_ads(brand: str | None = None):
    """Trigger Google Ads Transparency data collection."""
    # TODO: implement
    return {"status": "not_implemented"}
