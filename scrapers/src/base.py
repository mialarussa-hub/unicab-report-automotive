"""Base scraper class with common functionality."""

from abc import ABC, abstractmethod

import httpx


class BaseScraper(ABC):
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    @abstractmethod
    async def collect(self, brand: str, reference_month: int) -> list[dict]:
        """Collect data for a given brand and reference month."""
        ...

    async def close(self):
        await self.client.aclose()
