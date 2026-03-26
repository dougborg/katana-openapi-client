"""Text search utilities with tokenization, fuzzy matching, and relevance scoring.

Provides in-memory search capabilities modeled after the PostgreSQL trigram-based
search in katana-tools, adapted for client-side use with difflib.SequenceMatcher.

Usage:
    from katana_public_api_client.helpers.search import score_match, search_and_rank

    # Score a single item against a query
    score = score_match(
        query="fox fork",
        fields={
            "sku": ("FOX-FORK-160", 100),
            "name": ("Fox 36 Factory Fork", 30),
        },
    )

    # Search and rank a collection
    results = search_and_rank(
        query="fox fork",
        items=variants,
        field_extractor=lambda v: {
            "sku": (v.sku or "", 100),
            "name": (v.get_display_name(), 30),
        },
        limit=20,
    )
"""

from __future__ import annotations

from collections.abc import Callable
from difflib import SequenceMatcher

# Minimum similarity ratio for fuzzy matching (0.0 to 1.0)
# 0.65 catches common typos (stainles→stainless) while avoiding
# false positives like steel→sheet
FUZZY_THRESHOLD = 0.65


def _tokenize(text: str) -> list[str]:
    """Split text into lowercase tokens."""
    return text.lower().split()


def _similarity(a: str, b: str) -> float:
    """Calculate similarity ratio between two strings (0.0 to 1.0).

    Uses SequenceMatcher which is comparable to PostgreSQL's pg_trgm
    similarity() for short strings.
    """
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _best_token_similarity(token: str, text_tokens: list[str]) -> float:
    """Find the best similarity score for a token against any token in the text."""
    if not text_tokens:
        return 0.0
    return max(_similarity(token, t) for t in text_tokens)


def score_field(
    query_tokens: list[str],
    full_query: str,
    field_value: str,
    weight: int,
) -> float:
    """Score a single field against query tokens.

    Scoring tiers (as fraction of weight):
    - 1.0x: Exact match (full field == full query)
    - 0.8x: Field starts with query
    - 0.6x: All tokens found as substrings (AND logic)
    - 0.4x: All tokens fuzzy-match a field token (similarity > threshold)
    - 0.0x: No match

    Args:
        query_tokens: Lowercase query tokens.
        full_query: The full query string (lowercase).
        field_value: The field value to score against.
        weight: Maximum points this field can contribute.

    Returns:
        Score between 0.0 and weight.
    """
    if not field_value:
        return 0.0

    field_lower = field_value.lower()

    # Exact match
    if field_lower == full_query:
        return weight

    # Prefix match
    if field_lower.startswith(full_query):
        return weight * 0.8

    # All tokens as substrings
    if all(token in field_lower for token in query_tokens):
        return weight * 0.6

    # Fuzzy match: each query token must fuzzy-match at least one field token
    field_tokens = _tokenize(field_value)
    if field_tokens and all(
        _best_token_similarity(qt, field_tokens) >= FUZZY_THRESHOLD
        for qt in query_tokens
    ):
        # Scale by average similarity
        avg_sim = sum(
            _best_token_similarity(qt, field_tokens) for qt in query_tokens
        ) / len(query_tokens)
        return weight * 0.4 * avg_sim

    return 0.0


def score_match(
    query: str,
    fields: dict[str, tuple[str, int]],
) -> float:
    """Score an item against a search query across multiple fields.

    Args:
        query: The search query string.
        fields: Mapping of field_name -> (field_value, weight).
            Weight determines how many points this field can contribute.
            Higher weight = more important field.

    Returns:
        Total relevance score (sum across all fields). Zero means no match.

    Example:
        score = score_match(
            query="fox fork",
            fields={
                "sku": ("FOX-FORK-160", 100),
                "name": ("Fox 36 Factory Fork", 30),
            },
        )
    """
    query = query.strip()
    if not query:
        return 0.0

    query_lower = query.lower()
    query_tokens = _tokenize(query)
    if not query_tokens:
        return 0.0

    total = 0.0
    for _field_name, (value, weight) in fields.items():
        total += score_field(query_tokens, query_lower, value, weight)

    return total


def search_and_rank[T](
    query: str,
    items: list[T],
    field_extractor: Callable[[T], dict[str, tuple[str, int]]],
    limit: int = 50,
    min_score: float = 0.0,
) -> list[T]:
    """Search and rank items by relevance.

    Args:
        query: Search query string.
        items: List of items to search.
        field_extractor: Function that takes an item and returns a dict of
            field_name -> (field_value, weight) for scoring.
        limit: Maximum results to return.
        min_score: Minimum score threshold (default 0 = any match).

    Returns:
        Items sorted by relevance score (highest first), limited to top N.

    Example:
        results = search_and_rank(
            query="fox fork",
            items=all_variants,
            field_extractor=lambda v: {
                "sku": (v.sku or "", 100),
                "name": (v.get_display_name(), 30),
            },
            limit=20,
        )
    """
    query = query.strip()
    if not query:
        return []

    scored: list[tuple[T, float]] = []
    for item in items:
        fields = field_extractor(item)
        score = score_match(query, fields)
        if score > min_score:
            scored.append((item, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [item for item, _score in scored[:limit]]
