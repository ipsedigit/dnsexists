import os
import re
from datetime import date, timedelta

import requests


def fetch(args: dict) -> list[dict]:
    days = args.get("days", 30)
    limit = args.get("limit", 50)

    cutoff = (date.today() - timedelta(days=days)).isoformat()
    params = {
        "q": f"created:>{cutoff}",
        "sort": "stars",
        "order": "desc",
        "per_page": limit,
    }
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    resp = requests.get(
        "https://api.github.com/search/repositories",
        params=params,
        headers=headers,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"GitHub API error {resp.status_code}: {resp.text}")

    return [
        {
            "name": item["name"],
            "stars": item["stargazers_count"],
            "url": item["html_url"],
            "created_at": item["created_at"],
            "description": item["description"] or "",
        }
        for item in resp.json()["items"]
    ]


def select(candidates: list[dict]) -> list[str]:
    results = []
    for item in candidates:
        name = item["name"].lower()
        name = re.sub(r"[^a-z0-9-]", "-", name)
        name = name.strip("-")
        if len(name) < 3:
            continue
        if len(name) > 30:
            continue
        if name.isdigit():
            continue
        if name:
            results.append(name)
    return results
