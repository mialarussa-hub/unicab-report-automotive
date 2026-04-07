"""YouTube Data API v3 client for automotive sentiment collection."""

import os
import logging
from dataclasses import dataclass, field

import httpx

logger = logging.getLogger(__name__)

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"


@dataclass
class YouTubeVideo:
    video_id: str
    title: str
    description: str
    channel: str
    published_at: str
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    comments: list[str] = field(default_factory=list)
    url: str = ""

    def __post_init__(self):
        if not self.url:
            self.url = f"https://www.youtube.com/watch?v={self.video_id}"


@dataclass
class YouTubeResponse:
    videos: list[YouTubeVideo] = field(default_factory=list)
    error: str | None = None


class YouTubeClient:
    def __init__(self):
        self.api_key = os.environ.get("YOUTUBE_API_KEY", "")
        if not self.api_key:
            logger.warning("YOUTUBE_API_KEY not set — YouTube scraping will be disabled")
        self.client = httpx.AsyncClient(timeout=15.0)

    async def search_videos(self, query: str, max_results: int = 5) -> list[dict]:
        """Search YouTube for videos matching the query."""
        if not self.api_key:
            return []

        try:
            resp = await self.client.get(f"{YOUTUBE_API_BASE}/search", params={
                "part": "snippet",
                "q": query,
                "type": "video",
                "regionCode": "IT",
                "relevanceLanguage": "it",
                "maxResults": max_results,
                "key": self.api_key,
            })
            resp.raise_for_status()
            data = resp.json()
            return data.get("items", [])

        except Exception as e:
            logger.error(f"YouTube search error: {e}")
            return []

    async def get_video_details(self, video_ids: list[str]) -> dict:
        """Get video statistics and details."""
        if not self.api_key or not video_ids:
            return {}

        try:
            resp = await self.client.get(f"{YOUTUBE_API_BASE}/videos", params={
                "part": "snippet,statistics",
                "id": ",".join(video_ids),
                "key": self.api_key,
            })
            resp.raise_for_status()
            data = resp.json()

            result = {}
            for item in data.get("items", []):
                vid = item["id"]
                stats = item.get("statistics", {})
                result[vid] = {
                    "view_count": int(stats.get("viewCount", 0)),
                    "like_count": int(stats.get("likeCount", 0)),
                    "comment_count": int(stats.get("commentCount", 0)),
                }
            return result

        except Exception as e:
            logger.error(f"YouTube video details error: {e}")
            return {}

    async def get_comments(self, video_id: str, max_results: int = 10) -> list[str]:
        """Get top comments for a video."""
        if not self.api_key:
            return []

        try:
            resp = await self.client.get(f"{YOUTUBE_API_BASE}/commentThreads", params={
                "part": "snippet",
                "videoId": video_id,
                "maxResults": max_results,
                "order": "relevance",
                "key": self.api_key,
            })
            resp.raise_for_status()
            data = resp.json()

            comments = []
            for item in data.get("items", []):
                text = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                comments.append(text)
            return comments

        except Exception as e:
            logger.error(f"YouTube comments error for {video_id}: {e}")
            return []

    async def collect(self, query: str, max_videos: int = 5, max_comments: int = 10) -> YouTubeResponse:
        """Full collection: search + details + comments."""
        if not self.api_key:
            return YouTubeResponse(error="YOUTUBE_API_KEY not configured")

        try:
            # Search
            search_results = await self.search_videos(query, max_videos)
            if not search_results:
                return YouTubeResponse(error="No videos found")

            video_ids = [item["id"]["videoId"] for item in search_results]

            # Get details
            details = await self.get_video_details(video_ids)

            # Build video objects and fetch comments
            videos = []
            for item in search_results:
                vid = item["id"]["videoId"]
                snippet = item["snippet"]
                stats = details.get(vid, {})

                comments = await self.get_comments(vid, max_comments)

                videos.append(YouTubeVideo(
                    video_id=vid,
                    title=snippet.get("title", ""),
                    description=snippet.get("description", ""),
                    channel=snippet.get("channelTitle", ""),
                    published_at=snippet.get("publishedAt", ""),
                    view_count=stats.get("view_count", 0),
                    like_count=stats.get("like_count", 0),
                    comment_count=stats.get("comment_count", 0),
                    comments=comments,
                ))

            return YouTubeResponse(videos=videos)

        except Exception as e:
            logger.error(f"YouTube collect error: {e}")
            return YouTubeResponse(error=str(e))

    async def close(self):
        await self.client.aclose()
