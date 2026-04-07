"""Facebook Ads Library API wrapper for automotive ADV tracking."""

from scrapers.src.base import BaseScraper


class FacebookAdsScraper(BaseScraper):
    async def collect(self, brand: str, reference_month: int) -> list[dict]:
        # TODO: implement Facebook Ads Library API integration
        raise NotImplementedError
