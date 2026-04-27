#!/usr/bin/env bash
# fetch-review-threads.sh — Fetch all review threads on a PR with resolved status,
# paginated through both reviewThreads and per-thread comments so PRs with >100
# threads or >100 comments per thread are handled correctly.
# Usage: fetch-review-threads.sh <owner> <repo> <pr_number>
# Output: JSON array of threads, each with isResolved + comments[]

set -euo pipefail

owner="${1:?owner required}"
repo="${2:?repo required}"
number="${3:?pr number required}"

python3 - "$owner" "$repo" "$number" <<'PY'
import json
import subprocess
import sys

owner, repo, number = sys.argv[1], sys.argv[2], int(sys.argv[3])


def graphql(query, variables):
    cmd = ["gh", "api", "graphql", "-f", f"query={query}"]
    for key, value in variables.items():
        if value is None:
            continue
        cmd.extend(["-F", f"{key}={value}"])
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


THREADS_QUERY = """
query($owner: String!, $repo: String!, $number: Int!, $after: String) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      reviewThreads(first: 100, after: $after) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          isResolved
          comments(first: 100) {
            pageInfo { hasNextPage endCursor }
            nodes {
              id
              databaseId
              body
              path
              line
              author { login }
            }
          }
        }
      }
    }
  }
}
"""

THREAD_COMMENTS_QUERY = """
query($threadId: ID!, $after: String) {
  node(id: $threadId) {
    ... on PullRequestReviewThread {
      comments(first: 100, after: $after) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          databaseId
          body
          path
          line
          author { login }
        }
      }
    }
  }
}
"""

threads = []
after = None
while True:
    response = graphql(
        THREADS_QUERY,
        {"owner": owner, "repo": repo, "number": number, "after": after},
    )
    page = response["data"]["repository"]["pullRequest"]["reviewThreads"]
    for node in page["nodes"]:
        comments = node["comments"]
        threads.append(
            {
                "_thread_id": node["id"],
                "_comments_after": comments["pageInfo"]["endCursor"],
                "_comments_has_next": comments["pageInfo"]["hasNextPage"],
                "isResolved": node["isResolved"],
                "comments": comments["nodes"],
            }
        )
    if not page["pageInfo"]["hasNextPage"]:
        break
    after = page["pageInfo"]["endCursor"]

for thread in threads:
    while thread["_comments_has_next"]:
        response = graphql(
            THREAD_COMMENTS_QUERY,
            {"threadId": thread["_thread_id"], "after": thread["_comments_after"]},
        )
        page = response["data"]["node"]["comments"]
        thread["comments"].extend(page["nodes"])
        thread["_comments_after"] = page["pageInfo"]["endCursor"]
        thread["_comments_has_next"] = page["pageInfo"]["hasNextPage"]

output = [
    {"isResolved": t["isResolved"], "comments": t["comments"]} for t in threads
]
json.dump(output, sys.stdout)
sys.stdout.write("\n")
PY
