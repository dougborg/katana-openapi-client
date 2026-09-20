"""Release drafts need real Git refs before publish.yml can run."""

from email.message import Message
from unittest.mock import patch
from urllib.error import HTTPError

import pytest
from scripts.ensure_release_tags import ensure_release_tags

SHA = "a" * 40
OUTPUTS = {
    "paths_released": '[".", "katana_mcp_server"]',
    "tag_name": "client-v0.82.0",
    "sha": SHA,
    "katana_mcp_server--tag_name": "mcp-v0.116.0",
    "katana_mcp_server--sha": SHA,
}


def test_creates_both_draft_tags_at_exact_release_commit() -> None:
    missing = HTTPError("https://api.github.com", 404, "Not Found", Message(), None)
    with patch(
        "scripts.ensure_release_tags._api", side_effect=[missing, {}, missing, {}]
    ) as api:
        ensure_release_tags(OUTPUTS, "owner/repo", "test-token")
    posts = [c.args for c in api.call_args_list if c.args[0] == "POST"]
    assert [p[3] for p in posts] == [
        {"ref": "refs/tags/client-v0.82.0", "sha": SHA},
        {"ref": "refs/tags/mcp-v0.116.0", "sha": SHA},
    ]


def test_existing_matching_refs_are_noop() -> None:
    with patch(
        "scripts.ensure_release_tags._api",
        return_value={"object": {"sha": SHA, "type": "commit"}},
    ) as api:
        ensure_release_tags(OUTPUTS, "owner/repo", "test-token")
    assert all(c.args[0] == "GET" for c in api.call_args_list)


def test_existing_conflicting_ref_is_never_moved() -> None:
    with (
        patch(
            "scripts.ensure_release_tags._api",
            return_value={"object": {"sha": "b" * 40, "type": "commit"}},
        ) as api,
        pytest.raises(ValueError, match="Refusing to move"),
    ):
        ensure_release_tags(OUTPUTS, "owner/repo", "test-token")
    assert api.call_count == 1


def test_invalid_commit_fails_before_creating_any_tag() -> None:
    with (
        patch("scripts.ensure_release_tags._api") as api,
        pytest.raises(ValueError, match="exact commit SHA"),
    ):
        ensure_release_tags(
            {**OUTPUTS, "katana_mcp_server--sha": "main"}, "owner/repo", "test-token"
        )
    api.assert_not_called()


def test_permission_failure_does_not_attempt_create() -> None:
    forbidden = HTTPError("https://api.github.com", 403, "Forbidden", Message(), None)
    with (
        patch("scripts.ensure_release_tags._api", side_effect=forbidden) as api,
        pytest.raises(HTTPError),
    ):
        ensure_release_tags(OUTPUTS, "owner/repo", "test-token")
    assert api.call_count == 1
