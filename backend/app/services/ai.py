"""Claude API client for editorial content generation and sentiment analysis."""

import anthropic

from app.config import settings


def get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)


async def generate_editorial_comment(data: dict, context: str = "") -> str:
    """Generate an editorial comment for report data using Claude."""
    # TODO: implement with real prompt engineering
    raise NotImplementedError("AI editorial generation — to be implemented in AI layer sprint")


async def analyze_sentiment(text: str, brand: str) -> dict:
    """Analyze sentiment of a text snippet for a given brand."""
    # TODO: implement with real prompt engineering
    raise NotImplementedError("AI sentiment analysis — to be implemented in AI layer sprint")
