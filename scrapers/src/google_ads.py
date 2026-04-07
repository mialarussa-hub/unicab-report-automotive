"""Google Ads Transparency Center scraper for automotive ADV tracking."""

from scrapers.src.base import BaseScraper


class GoogleAdsScraper(BaseScraper):
    async def collect(self, brand: str, reference_month: int) -> list[dict]:
        # TODO: implement Google Ads Transparency Center scraping
        raise NotImplementedError
