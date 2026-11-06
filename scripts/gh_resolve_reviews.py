#!/usr/bin/env python3
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
gh_resolve_reviews.py: GraphQL PR Review Thread Triage & Resolver for Bean-Brewer.

Provides programmatic helpers and a CLI to:
1. Parse GraphQL `reviewThreads` JSON payloads (or fetch live via `gh api graphql`).
2. Filter out untrusted commenters (`authorAssociation` must be in
   `{"OWNER", "MEMBER", "COLLABORATOR"}` unless `--allow-all` is set).
3. Render a Markdown Four-Verdict Table:
   `| Thread ID | File:Line | Author | Comment Summary | Recommended Verdict (fix/reject/defer/ask) | Rationale |`
4. Generate GraphQL `resolveReviewThread` mutations strictly for `fix` and `reject` verdicts.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from typing import Any, Dict, List, Optional

TRUSTED_ASSOCIATIONS = {"OWNER", "MEMBER", "COLLABORATOR"}
VALID_VERDICTS = {"fix", "reject", "defer", "ask"}
RESOLVABLE_VERDICTS = {"fix", "reject"}

REVIEW_THREADS_QUERY = """
query($owner: String!, $name: String!, $pr: Int!) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $pr) {
      reviewThreads(first: 100) {
        nodes {
          id
          isResolved
          path
          line
          comments(first: 20) {
            nodes {
              id
              body
              author {
                login
              }
              authorAssociation
            }
          }
        }
      }
    }
  }
}
""".strip()


def infer_verdict_and_rationale(comment_body: str, explicit_verdict: Optional[str] = None, explicit_rationale: Optional[str] = None) -> tuple[str, str]:
    """Determines a default recommended verdict (fix/reject/defer/ask) and rationale."""
    if explicit_verdict and explicit_verdict.lower() in VALID_VERDICTS:
        v = explicit_verdict.lower()
        r = explicit_rationale or f"Explicitly classified as '{v}'."
        return v, r

    lower = (comment_body or "").lower()
    if any(k in lower for k in ("nit:", "out of scope", "follow-up", "followup", "later pr", "future pr", "defer")):
        return "defer", explicit_rationale or "Non-blocking nit or out-of-scope follow-up item."
    if "?" in lower and any(k in lower for k in ("should we", "product decision", "clarify", "which approach", "ask")):
        return "ask", explicit_rationale or "Requires human maintainer or product clarification."
    if any(k in lower for k in ("false positive", "intentional", "by design", "disagree", "not applicable", "reject")):
        return "reject", explicit_rationale or "Behavior is intentional per approved specification."
    return "fix", explicit_rationale or "Actionable defect or review improvement to address in slice."


def extract_raw_threads(payload: Any) -> List[Dict[str, Any]]:
    """Extracts the list of raw reviewThread nodes from nested GraphQL JSON or a flat list."""
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []

    if "reviewThreads" in payload:
        rt = payload["reviewThreads"]
        if isinstance(rt, list):
            return rt
        if isinstance(rt, dict) and isinstance(rt.get("nodes"), list):
            return rt["nodes"]

    if "nodes" in payload and isinstance(payload["nodes"], list):
        return payload["nodes"]

    data = payload.get("data", payload)
    repo = data.get("repository", {}) if isinstance(data, dict) else {}
    pr = repo.get("pullRequest", {}) if isinstance(repo, dict) else {}
    rt = pr.get("reviewThreads", {}) if isinstance(pr, dict) else {}
    if isinstance(rt, dict) and isinstance(rt.get("nodes"), list):
        return rt["nodes"]
    if isinstance(rt, list):
        return rt

    return []


def parse_review_threads(
    payload: Any,
    allow_all: bool = False,
    include_resolved: bool = False,
) -> List[Dict[str, Any]]:
    """Parses GraphQL reviewThreads and filters out untrusted commenters unless allow_all=True."""
    raw_nodes = extract_raw_threads(payload)
    parsed_threads: List[Dict[str, Any]] = []

    for node in raw_nodes:
        if not isinstance(node, dict):
            continue
        if node.get("isResolved") and not include_resolved:
            continue

        comments_container = node.get("comments", [])
        if isinstance(comments_container, dict):
            comments = comments_container.get("nodes", [])
        elif isinstance(comments_container, list):
            comments = comments_container
        else:
            comments = []

        first_comment = comments[0] if comments else {}
        association = (
            first_comment.get("authorAssociation")
            or node.get("authorAssociation")
            or "NONE"
        ).upper()

        if not allow_all and association not in TRUSTED_ASSOCIATIONS:
            continue

        author_obj = first_comment.get("author") or node.get("author") or {}
        if isinstance(author_obj, dict):
            author = author_obj.get("login") or "unknown"
        else:
            author = str(author_obj)

        body = (first_comment.get("body") or node.get("body") or "").strip()
        summary = " ".join(body.splitlines()).strip()
        if len(summary) > 120:
            summary = summary[:117] + "..."

        path = node.get("path") or first_comment.get("path") or "unknown"
        line = node.get("line") or node.get("originalLine") or first_comment.get("line") or 1
        file_line = f"{path}:{line}"

        verdict, rationale = infer_verdict_and_rationale(
            body,
            explicit_verdict=node.get("verdict") or node.get("recommended_verdict"),
            explicit_rationale=node.get("rationale"),
        )

        parsed_threads.append({
            "id": node.get("id") or "PRRT_unknown",
            "thread_id": node.get("id") or "PRRT_unknown",
            "path": path,
            "line": line,
            "file_line": file_line,
            "author": author,
            "authorAssociation": association,
            "body": body,
            "summary": summary,
            "verdict": verdict,
            "rationale": rationale,
            "isResolved": bool(node.get("isResolved", False)),
        })

    return parsed_threads


def filter_trusted_threads(
    threads: List[Dict[str, Any]],
    allow_all: bool = False,
) -> List[Dict[str, Any]]:
    """Filters a list of thread dicts by trusted authorAssociation."""
    return parse_review_threads(threads, allow_all=allow_all)


def format_four_verdict_table(threads: List[Dict[str, Any]]) -> str:
    """Formats parsed review threads into the canonical Markdown Four-Verdict Table."""
    header = (
        "| Thread ID | File:Line | Author | Comment Summary | Recommended Verdict (fix/reject/defer/ask) | Rationale |\n"
        "| :--- | :--- | :--- | :--- | :---: | :--- |"
    )
    if not threads:
        return header + "\n| *(none)* | - | - | No actionable trusted review threads | - | - |"

    rows = [header]
    for t in threads:
        tid = t.get("thread_id") or t.get("id") or "PRRT_unknown"
        file_line = t.get("file_line") or f"{t.get('path', 'unknown')}:{t.get('line', 1)}"
        author = t.get("author") or "unknown"
        summary = (t.get("summary") or t.get("body") or "").replace("|", "\\|").replace("\n", " ").strip()
        verdict = (t.get("verdict") or t.get("recommended_verdict") or "fix").lower()
        rationale = (t.get("rationale") or f"Recommended '{verdict}' disposition.").replace("|", "\\|").strip()
        rows.append(
            f"| `{tid}` | `{file_line}` | @{author} | {summary} | `{verdict}` | {rationale} |"
        )
    return "\n".join(rows)


def build_resolve_mutations(threads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Builds GraphQL `resolveReviewThread` mutations strictly for `fix` and `reject` verdicts."""
    mutations: List[Dict[str, Any]] = []
    for t in threads:
        verdict = (t.get("verdict") or t.get("recommended_verdict") or "").lower()
        if verdict not in RESOLVABLE_VERDICTS:
            continue
        tid = t.get("thread_id") or t.get("id")
        if not tid:
            continue
        query = (
            f'mutation {{ resolveReviewThread(input: {{threadId: "{tid}"}}) '
            f"{{ thread {{ id isResolved }} }} }}"
        )
        mutations.append({
            "thread_id": tid,
            "verdict": verdict,
            "query": query,
            "variables": {"threadId": tid},
        })
    return mutations


def fetch_review_threads_from_github(owner: str, name: str, pr_number: int) -> Dict[str, Any]:
    """Fetches reviewThreads via `gh api graphql`."""
    cmd = [
        "gh", "api", "graphql",
        "-f", f"query={REVIEW_THREADS_QUERY}",
        "-F", f"owner={owner}",
        "-F", f"name={name}",
        "-F", f"pr={pr_number}",
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True)
    return json.loads(res.stdout)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="GraphQL PR Review Thread Resolver (Four-Verdict Model)")
    parser.add_argument("--input", help="Path to JSON file containing GraphQL reviewThreads payload")
    parser.add_argument("--repo", help="GitHub repository in OWNER/REPO format (for live fetch)")
    parser.add_argument("--pr", type=int, help="Pull Request number (for live fetch)")
    parser.add_argument("--allow-all", action="store_true", help="Include untrusted commenter associations")
    parser.add_argument("--include-resolved", action="store_true", help="Include already-resolved threads")
    parser.add_argument("--json", action="store_true", help="Emit JSON output with table and GraphQL mutations")

    args = parser.parse_args(argv)

    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            payload = json.load(f)
    elif args.repo and args.pr:
        if "/" not in args.repo:
            sys.stderr.write("[ERROR] --repo must be in OWNER/REPO format.\n")
            return 1
        owner, name = args.repo.split("/", 1)
        payload = fetch_review_threads_from_github(owner, name, args.pr)
    else:
        sys.stderr.write("[ERROR] Specify either --input <json_path> or --repo <OWNER/REPO> --pr <NUM>.\n")
        return 1

    threads = parse_review_threads(
        payload,
        allow_all=args.allow_all,
        include_resolved=args.include_resolved,
    )
    table_md = format_four_verdict_table(threads)
    mutations = build_resolve_mutations(threads)

    if args.json:
        print(json.dumps({
            "threads": threads,
            "table_markdown": table_md,
            "resolve_mutations": mutations,
        }, indent=2))
    else:
        print(table_md)

    return 0


if __name__ == "__main__":
    sys.exit(main())
