"""Reddit scraper for automotive subreddits sentiment."""

from src.base import BaseScraper


class RedditScraper(BaseScraper):
    async def collect(self, brand: str, reference_month: int) -> list[dict]:
        # TODO: implement Reddit API / scraping
        raise NotImplementedError
