"""Tests for the search utility module."""

import pytest

from katana_public_api_client.helpers.search import (
    score_field,
    score_match,
    search_and_rank,
)


class TestScoreField:
    """Tests for individual field scoring."""

    def test_exact_match_gets_full_weight(self) -> None:
        score = score_field(["fox-fork-160"], "fox-fork-160", "FOX-FORK-160", 100)
        assert score == 100

    def test_prefix_match_gets_80_percent(self) -> None:
        score = score_field(["fox"], "fox", "FOX-FORK-160", 100)
        assert score == pytest.approx(80)

    def test_substring_match_gets_60_percent(self) -> None:
        score = score_field(["fork", "160"], "fork 160", "FOX-FORK-160", 100)
        assert score == pytest.approx(60)

    def test_fuzzy_match_returns_positive_score(self) -> None:
        # "stainles" is close to "stainless"
        score = score_field(["stainles"], "stainles", "Stainless Steel Sheet", 100)
        assert score > 0

    def test_no_match_returns_zero(self) -> None:
        score = score_field(["aluminum"], "aluminum", "Stainless Steel", 100)
        assert score == 0

    def test_empty_field_returns_zero(self) -> None:
        score = score_field(["fox"], "fox", "", 100)
        assert score == 0

    def test_multi_word_substring_all_tokens_must_match(self) -> None:
        # Both "steel" and "sheet" must appear
        score = score_field(
            ["steel", "sheet"], "steel sheet", "Stainless Steel Sheet", 100
        )
        assert score == pytest.approx(60)

    def test_multi_word_partial_match_returns_zero(self) -> None:
        # "steel" matches but "aluminum" doesn't
        score = score_field(
            ["steel", "aluminum"], "steel aluminum", "Stainless Steel Sheet", 100
        )
        assert score == 0

    def test_word_order_does_not_matter(self) -> None:
        score = score_field(
            ["sheet", "steel"], "sheet steel", "Stainless Steel Sheet", 100
        )
        assert score == pytest.approx(60)


class TestScoreMatch:
    """Tests for multi-field scoring."""

    def test_exact_sku_scores_highest(self) -> None:
        score = score_match(
            query="FOX-FORK-160",
            fields={
                "sku": ("FOX-FORK-160", 100),
                "name": ("Fox 36 Factory Fork", 30),
            },
        )
        assert score >= 100

    def test_name_match_adds_to_score(self) -> None:
        score_with_name = score_match(
            query="fox",
            fields={
                "sku": ("FOX-FORK-160", 100),
                "name": ("Fox 36 Factory Fork", 30),
            },
        )
        score_without_name = score_match(
            query="fox",
            fields={
                "sku": ("FOX-FORK-160", 100),
                "name": ("", 30),
            },
        )
        assert score_with_name > score_without_name

    def test_empty_query_returns_zero(self) -> None:
        assert score_match(query="", fields={"name": ("Test", 100)}) == 0

    def test_whitespace_query_returns_zero(self) -> None:
        assert score_match(query="   ", fields={"name": ("Test", 100)}) == 0

    def test_no_matching_fields_returns_zero(self) -> None:
        assert (
            score_match(
                query="xyz",
                fields={
                    "sku": ("ABC-123", 100),
                    "name": ("Widget", 30),
                },
            )
            == 0
        )

    def test_fuzzy_typo_tolerance(self) -> None:
        """A common typo should still match via fuzzy."""
        score = score_match(
            query="stainles steel",
            fields={"name": ("Stainless Steel Sheet", 100)},
        )
        assert score > 0

    def test_case_insensitive(self) -> None:
        score = score_match(
            query="FOX FORK",
            fields={"name": ("fox fork suspension", 100)},
        )
        assert score > 0


class TestSearchAndRank:
    """Tests for the full search pipeline."""

    def test_returns_matching_items_ranked(self) -> None:
        items = ["Stainless Steel Sheet", "Carbon Steel Rod", "Aluminum Sheet"]
        results = search_and_rank(
            query="steel",
            items=items,
            field_extractor=lambda x: {"name": (x, 100)},
        )
        assert len(results) == 2
        assert "Stainless Steel Sheet" in results
        assert "Carbon Steel Rod" in results

    def test_exact_match_ranked_first(self) -> None:
        items = ["FOX-FORK-160", "FOX-SHOCK-200", "SHIMANO-XT"]
        results = search_and_rank(
            query="FOX-FORK-160",
            items=items,
            field_extractor=lambda x: {"sku": (x, 100)},
        )
        assert results[0] == "FOX-FORK-160"

    def test_respects_limit(self) -> None:
        items = [f"Item {i}" for i in range(100)]
        results = search_and_rank(
            query="item",
            items=items,
            field_extractor=lambda x: {"name": (x, 100)},
            limit=5,
        )
        assert len(results) == 5

    def test_empty_query_returns_empty(self) -> None:
        results = search_and_rank(
            query="",
            items=["a", "b"],
            field_extractor=lambda x: {"name": (x, 100)},
        )
        assert results == []

    def test_fuzzy_matching_finds_typos(self) -> None:
        items = ["Kitchen Knife", "Stainless Steel", "Aluminum Sheet"]
        results = search_and_rank(
            query="knif",
            items=items,
            field_extractor=lambda x: {"name": (x, 100)},
        )
        assert "Kitchen Knife" in results

    def test_multi_word_query(self) -> None:
        items = [
            "Sheet of Steel",
            "Steel Rod",
            "Aluminum Sheet",
            "Carbon Steel Sheet",
        ]
        results = search_and_rank(
            query="steel sheet",
            items=items,
            field_extractor=lambda x: {"name": (x, 100)},
        )
        # Both tokens must match
        assert "Sheet of Steel" in results
        assert "Carbon Steel Sheet" in results
        assert "Steel Rod" not in results
        assert "Aluminum Sheet" not in results

    def test_multi_field_scoring(self) -> None:
        """Items matching on high-weight fields should rank higher."""
        items = [
            {"sku": "STEEL-001", "name": "Widget"},
            {"sku": "WIDGET-001", "name": "Steel Rod"},
        ]
        results = search_and_rank(
            query="steel",
            items=items,
            field_extractor=lambda x: {
                "sku": (x["sku"], 100),
                "name": (x["name"], 30),
            },
        )
        # SKU match (weight 100) should rank higher than name match (weight 30)
        assert results[0]["sku"] == "STEEL-001"
