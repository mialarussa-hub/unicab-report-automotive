"""Reddit client — uses PullPush.io archive API (works from datacenter IPs).

Reddit's native API blocks datacenter IPs (403 from Hetzner).
PullPush.io is a free Reddit archive that provides:
- Post search by subreddit + query
- Comment retrieval by post ID
- No authentication required, no IP restrictions
"""

import time
import logging
from dataclasses import dataclass, field

import httpx

logger = logging.getLogger(__name__)

PULLPUSH_BASE = "https://api.pullpush.io/reddit"
USER_AGENT = "UNICABAutomotiveResearch/1.0"

# Filter: only posts from the last N months
MAX_AGE_SECONDS = 365 * 24 * 3600  # 12 months


@dataclass
class RedditComment:
    author: str
    text: str
    score: int
    created_utc: float = 0


@dataclass
class RedditPost:
    post_id: str
    title: str
    selftext: str
    author: str
    score: int
    num_comments: int
    url: str
    subreddit: str
    created_utc: float = 0
    comments: list[RedditComment] = field(default_factory=list)


@dataclass
class RedditResponse:
    posts: list[RedditPost] = field(default_factory=list)
    error: str | None = None


class RedditClient:
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=20.0,
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
        )

    async def search_subreddit(
        self, subreddit: str, query: str, limit: int = 10,
    ) -> RedditResponse:
        """Search a subreddit via PullPush.io archive API."""
        try:
            # Calculate timestamp for "after" filter (last 12 months)
            after_ts = int(time.time()) - MAX_AGE_SECONDS

            url = f"{PULLPUSH_BASE}/search/submission/"
            resp = await self.client.get(url, params={
                "subreddit": subreddit,
                "q": query,
                "size": limit,
                "sort": "desc",
                "sort_type": "created_utc",
                "after": after_ts,
            })
            resp.raise_for_status()
            data = resp.json()

            posts = []
            for p in data.get("data", []):
                posts.append(RedditPost(
                    post_id=p.get("id", ""),
                    title=p.get("title", ""),
                    selftext=p.get("selftext", ""),
                    author=p.get("author", "[deleted]"),
                    score=p.get("score", 0),
                    num_comments=p.get("num_comments", 0),
                    url=f"https://www.reddit.com{p.get('permalink', '')}",
                    subreddit=p.get("subreddit", subreddit),
                    created_utc=p.get("created_utc", 0),
                ))

            return RedditResponse(posts=posts)

        except Exception as e:
            logger.error(f"PullPush search error for r/{subreddit} '{query}': {e}")
            return RedditResponse(error=str(e))

    async def get_post_comments(self, post_id: str, limit: int = 30) -> list[RedditComment]:
        """Get comments for a post via PullPush.io."""
        try:
            url = f"{PULLPUSH_BASE}/search/comment/"
            resp = await self.client.get(url, params={
                "link_id": post_id,
                "size": limit,
                "sort": "desc",
                "sort_type": "score",
            })
            resp.raise_for_status()
            data = resp.json()

            comments = []
            for c in data.get("data", []):
                body = c.get("body", "")
                author = c.get("author", "[deleted]")

                # Skip deleted/removed/bot comments
                if not body or author == "[deleted]" or body == "[removed]":
                    continue
                if author.lower() in ("automoderator", "bot"):
                    continue

                comments.append(RedditComment(
                    author=author,
                    text=body,
                    score=c.get("score", 0),
                    created_utc=c.get("created_utc", 0),
                ))

            return comments

        except Exception as e:
            logger.error(f"PullPush comments error for post {post_id}: {e}")
            return []

    async def collect(
        self, subreddit: str, query: str, max_posts: int = 10, max_comments: int = 30,
    ) -> RedditResponse:
        """Full collection: search posts + fetch comments for each."""
        search_resp = await self.search_subreddit(subreddit, query, limit=max_posts)

        if search_resp.error:
            return search_resp

        if not search_resp.posts:
            return RedditResponse(error=f"No posts found in r/{subreddit} for '{query}'")

        # Fetch comments for posts that have comments
        for post in search_resp.posts:
            if post.num_comments > 0:
                post.comments = await self.get_post_comments(
                    post.post_id, limit=max_comments,
                )
                logger.warning(
                    f"[Reddit] r/{subreddit} post '{post.title[:50]}': "
                    f"{len(post.comments)} comments fetched"
                )

        return search_resp

    async def close(self):
        await self.client.aclose()
