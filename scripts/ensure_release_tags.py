"""Create Git refs for release-please drafts so tag-triggered publishing runs.

GitHub draft releases do not create tags. Keep releases in draft until publish.yml
has uploaded artifacts, but create their refs at release-please's exact commit SHA.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def _api(method: str, path: str, token: str, body: dict[str, str] | None = None) -> Any:
    request = Request(
        f"https://api.github.com/{path}",
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def ensure_release_tags(outputs: dict[str, str], repository: str, token: str) -> None:
    """Create missing refs; refuse to move an existing tag to another commit."""
    releases = []
    for path in json.loads(outputs.get("paths_released", "[]")):
        prefix = "" if path == "." else f"{path}--"
        tag = outputs[f"{prefix}tag_name"]
        sha = outputs[f"{prefix}sha"]
        if not re.fullmatch(r"(?:client|mcp)-v\d+\.\d+\.\d+", tag):
            raise ValueError(f"Unexpected release tag: {tag}")
        if not re.fullmatch(r"[0-9a-f]{40}", sha):
            raise ValueError(f"Release {tag} must identify an exact commit SHA")
        releases.append((tag, sha))
    for tag, sha in releases:
        try:
            existing = _api("GET", f"repos/{repository}/git/ref/tags/{tag}", token)
        except HTTPError as exc:
            if exc.code != 404:
                raise
            _api(
                "POST",
                f"repos/{repository}/git/refs",
                token,
                {"ref": f"refs/tags/{tag}", "sha": sha},
            )
            print(f"Created {tag} at {sha}")
        else:
            if (
                existing["object"]["sha"] != sha
                or existing["object"]["type"] != "commit"
            ):
                raise ValueError(f"Refusing to move existing release tag {tag}")
            print(f"{tag} already points to {sha}")


if __name__ == "__main__":
    ensure_release_tags(
        outputs=json.loads(os.environ["RELEASE_OUTPUTS"]),
        repository=os.environ["GITHUB_REPOSITORY"],
        token=os.environ["GH_TOKEN"],
    )
