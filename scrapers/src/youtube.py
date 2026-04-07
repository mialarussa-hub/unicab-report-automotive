"""YouTube Data API v3 wrapper for automotive sentiment collection."""

from scrapers.src.base import BaseScraper


class YouTubeScraper(BaseScraper):
    async def collect(self, brand: str, reference_month: int) -> list[dict]:
        # TODO: implement YouTube Data API v3 integration
        raise NotImplementedError
