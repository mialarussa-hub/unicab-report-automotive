"""Reddit client — uses Arctic Shift archive API (works from datacenter IPs).

Reddit's native API blocks datacenter IPs (403 from Hetzner).
Arctic Shift is a comprehensive Reddit archive with better search than PullPush:
- Post search by subreddit + query/title
- Comment retrieval by post ID (link_id)
- No authentication required, no IP restrictions
"""

import logging
from dataclasses import dataclass, field

import httpx

logger = logging.getLogger(__name__)

ARCTIC_SHIFT_BASE = "https://arctic-shift.photon-reddit.com/api"
USER_AGENT = "UNICABAutomotiveResearch/1.0"


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
        self, subreddit: str, query: str, limit: int = 25,
    ) -> RedditResponse:
        """Search a subreddit via Arctic Shift archive API.

        Uses 'title' search for better matching — Reddit users type short titles
        like "Golf" not "Volkswagen Golf".
        """
        try:
            url = f"{ARCTIC_SHIFT_BASE}/posts/search"
            resp = await self.client.get(url, params={
                "subreddit": subreddit,
                "title": query,
                "limit": str(limit),
            })
            resp.raise_for_status()
            data = resp.json()

            posts = []
            for p in data.get("data", []):
                permalink = p.get("permalink", "")
                posts.append(RedditPost(
                    post_id=p.get("id", ""),
                    title=p.get("title", ""),
                    selftext=p.get("selftext") or "",
                    author=p.get("author", "[deleted]"),
                    score=p.get("score", 0),
                    num_comments=p.get("num_comments", 0),
                    url=f"https://www.reddit.com{permalink}" if permalink else "",
                    subreddit=p.get("subreddit", subreddit),
                    created_utc=p.get("created_utc", 0),
                ))

            return RedditResponse(posts=posts)

        except Exception as e:
            logger.error(f"Arctic Shift search error for r/{subreddit} '{query}': {e}")
            return RedditResponse(error=str(e))

    async def get_post_comments(self, post_id: str, limit: int = 50) -> list[RedditComment]:
        """Get comments for a post via Arctic Shift."""
        try:
            url = f"{ARCTIC_SHIFT_BASE}/comments/search"
            resp = await self.client.get(url, params={
                "link_id": post_id,
                "limit": str(limit),
            })
            resp.raise_for_status()
            data = resp.json()

            comments = []
            for c in data.get("data", []):
                body = c.get("body") or ""
                author = c.get("author", "[deleted]")

                # Skip deleted/removed/bot comments
                if not body or author == "[deleted]" or body == "[removed]":
                    continue
                if author.lower() in ("automoderator", "bot", "sneakpeekbot"):
                    continue
                # Skip very short noise
                if len(body.strip()) < 5:
                    continue

                comments.append(RedditComment(
                    author=author,
                    text=body,
                    score=c.get("score", 0),
                    created_utc=c.get("created_utc", 0),
                ))

            return comments

        except Exception as e:
            logger.error(f"Arctic Shift comments error for post {post_id}: {e}")
            return []

    async def collect(
        self,
        subreddit: str,
        queries: list[str],
        max_posts: int = 25,
        max_comments: int = 50,
        min_comments: int = 2,
    ) -> RedditResponse:
        """Full collection: search with multiple queries + fetch comments.

        Args:
            subreddit: target subreddit
            queries: list of search terms (e.g. ["golf", "VW golf", "volkswagen golf"])
            max_posts: max posts per query
            max_comments: max comments to fetch per post
            min_comments: skip posts with fewer comments than this
        """
        all_posts = {}  # post_id -> post

        for query in queries:
            logger.warning(f"[Reddit] Searching r/{subreddit} title='{query}'")
            response = await self.search_subreddit(subreddit, query, limit=max_posts)

            if response.error:
                logger.warning(f"[Reddit] Search error: {response.error}")
                continue

            for post in response.posts:
                if post.post_id not in all_posts:
                    all_posts[post.post_id] = post

        if not all_posts:
            return RedditResponse(error=f"No posts found in r/{subreddit}")

        # Sort by num_comments descending — scrape the most active threads first
        sorted_posts = sorted(all_posts.values(), key=lambda p: p.num_comments, reverse=True)

        # Fetch comments for posts with enough comments
        fetched = 0
        for post in sorted_posts:
            if post.num_comments < min_comments:
                continue

            post.comments = await self.get_post_comments(post.post_id, limit=max_comments)
            fetched += 1
            logger.warning(
                f"[Reddit] r/{subreddit} '{post.title[:50]}': "
                f"{len(post.comments)} comments (of {post.num_comments})"
            )

        # Only return posts that have comments
        posts_with_comments = [p for p in sorted_posts if p.comments]

        logger.warning(
            f"[Reddit] r/{subreddit}: {len(all_posts)} posts found, "
            f"{fetched} fetched, {len(posts_with_comments)} with comments"
        )

        return RedditResponse(posts=posts_with_comments)

    async def close(self):
        await self.client.aclose()
