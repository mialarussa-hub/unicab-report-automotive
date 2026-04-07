"""YouTube scraper for automotive sentiment collection."""

import logging
from dataclasses import dataclass, field

from scrapers.src.youtube_client import YouTubeClient

logger = logging.getLogger(__name__)

QUERY_TEMPLATES = [
    "{brand} {model} recensione",
    "{brand} {model} prova su strada",
]


@dataclass
class YouTubeResult:
    video_id: str
    title: str
    channel: str
    url: str
    view_count: int = 0
    like_count: int = 0
    description: str = ""
    comments: list[str] = field(default_factory=list)


@dataclass
class YouTubeResponse:
    results: list[YouTubeResult] = field(default_factory=list)
    error: str | None = None


async def scrape_youtube(brand: str, model: str = "") -> YouTubeResponse:
    """Search YouTube for automotive reviews and collect comments."""
    client = YouTubeClient()

    try:
        all_results: list[YouTubeResult] = []
        seen_ids = set()

        for template in QUERY_TEMPLATES:
            query = template.format(brand=brand, model=model or "").strip()
            response = await client.collect(query, max_videos=3, max_comments=10)

            if response.error:
                logger.warning(f"YouTube error for '{query}': {response.error}")
                continue

            for video in response.videos:
                if video.video_id not in seen_ids:
                    seen_ids.add(video.video_id)
                    all_results.append(YouTubeResult(
                        video_id=video.video_id,
                        title=video.title,
                        channel=video.channel,
                        url=video.url,
                        view_count=video.view_count,
                        like_count=video.like_count,
                        description=video.description[:500],
                        comments=video.comments[:10],
                    ))

        if not all_results:
            return YouTubeResponse(error="No YouTube results found (API key may not be configured)")

        return YouTubeResponse(results=all_results)

    except Exception as e:
        logger.error(f"YouTube scrape error: {e}")
        return YouTubeResponse(error=str(e))
    finally:
        await client.close()
