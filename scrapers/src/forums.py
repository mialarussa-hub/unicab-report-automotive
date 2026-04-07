"""Forum scraper for Italian automotive forums."""

from scrapers.src.base import BaseScraper


class ForumScraper(BaseScraper):
    async def collect(self, brand: str, reference_month: int) -> list[dict]:
        # TODO: implement forum scraping (clubalfa.it, forum.quattroruote.it, etc.)
        raise NotImplementedError
