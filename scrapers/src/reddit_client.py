"""Reddit API client — direct JSON API, no authentication required."""

import logging
from dataclasses import dataclass, field

import httpx

logger = logging.getLogger(__name__)

REDDIT_BASE = "https://www.reddit.com"
USER_AGENT = "UNICAB-Automotive-Scraper/1.0"


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
            timeout=15.0,
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
        )

    async def search_subreddit(self, subreddit: str, query: str, limit: int = 10, sort: str = "relevance") -> RedditResponse:
        """Search a subreddit for posts matching a query."""
        try:
            url = f"{REDDIT_BASE}/r/{subreddit}/search.json"
            resp = await self.client.get(url, params={
                "q": query,
                "restrict_sr": "on",
                "sort": sort,
                "limit": limit,
                "t": "year",  # last year
            })
            resp.raise_for_status()
            data = resp.json()

            posts = []
            for child in data.get("data", {}).get("children", []):
                post_data = child.get("data", {})
                posts.append(RedditPost(
                    post_id=post_data.get("id", ""),
                    title=post_data.get("title", ""),
                    selftext=post_data.get("selftext", ""),
                    author=post_data.get("author", "[deleted]"),
                    score=post_data.get("score", 0),
                    num_comments=post_data.get("num_comments", 0),
                    url=f"https://www.reddit.com{post_data.get('permalink', '')}",
                    subreddit=post_data.get("subreddit", subreddit),
                    created_utc=post_data.get("created_utc", 0),
                ))

            return RedditResponse(posts=posts)

        except Exception as e:
            logger.error(f"Reddit search error for r/{subreddit} '{query}': {e}")
            return RedditResponse(error=str(e))

    async def get_post_comments(self, permalink: str, limit: int = 25) -> list[RedditComment]:
        """Get comments for a specific post."""
        try:
            # permalink is like /r/ItalyMotori/comments/abc123/title/
            clean_path = permalink.rstrip("/")
            url = f"{REDDIT_BASE}{clean_path}.json"
            resp = await self.client.get(url, params={
                "limit": limit,
                "sort": "top",
                "depth": 2,
            })
            resp.raise_for_status()
            data = resp.json()

            comments = []
            # data[1] contains the comments listing
            if len(data) > 1:
                comment_listing = data[1].get("data", {}).get("children", [])
                comments = self._extract_comments(comment_listing, max_depth=2)

            return comments

        except Exception as e:
            logger.error(f"Reddit comments error for {permalink}: {e}")
            return []

    def _extract_comments(self, children: list, max_depth: int = 2, current_depth: int = 0) -> list[RedditComment]:
        """Recursively extract comments from Reddit API response."""
        comments = []
        if current_depth >= max_depth:
            return comments

        for child in children:
            if child.get("kind") != "t1":
                continue

            data = child.get("data", {})
            body = data.get("body", "")
            author = data.get("author", "[deleted]")

            if body and author != "[deleted]" and body != "[removed]":
                comments.append(RedditComment(
                    author=author,
                    text=body,
                    score=data.get("score", 0),
                    created_utc=data.get("created_utc", 0),
                ))

            # Recurse into replies
            replies = data.get("replies")
            if isinstance(replies, dict):
                reply_children = replies.get("data", {}).get("children", [])
                comments.extend(self._extract_comments(reply_children, max_depth, current_depth + 1))

        return comments

    async def collect(self, subreddit: str, query: str, max_posts: int = 5, max_comments: int = 20) -> RedditResponse:
        """Full collection: search + fetch comments for top posts."""
        search_resp = await self.search_subreddit(subreddit, query, limit=max_posts)

        if search_resp.error:
            return search_resp

        if not search_resp.posts:
            return RedditResponse(error=f"No posts found in r/{subreddit} for '{query}'")

        # Fetch comments for each post
        for post in search_resp.posts:
            permalink = post.url.replace("https://www.reddit.com", "")
            post.comments = await self.get_post_comments(permalink, limit=max_comments)

        return search_resp

    async def close(self):
        await self.client.aclose()
