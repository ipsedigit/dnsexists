import logging
import os
import re
from datetime import date, datetime, timedelta, timezone

import requests

logger = logging.getLogger(__name__)

_TIMEOUT = 10

DEFAULT_WEIGHTS = {
    "github": 1.0,
    "hn": 0.8,
    "producthunt": 0.7,
    "reddit": 0.6,
}

_SUBREDDITS = ["programming", "webdev", "MachineLearning"]


def _normalize(name: str) -> str:
    name = name.lower()
    name = re.sub(r"[^a-z0-9-]", "-", name)
    return name.strip("-")


def _fetch_github(days: int, limit: int) -> list[dict]:
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        resp = requests.get(
            "https://api.github.com/search/repositories",
            params={"q": f"created:>{cutoff}", "sort": "stars", "order": "desc", "per_page": limit},
            headers=headers,
            timeout=_TIMEOUT,
        )
    except Exception as exc:
        logger.warning("GitHub fetch failed: %s", exc)
        return []
    if resp.status_code != 200:
        logger.warning("GitHub API error %s", resp.status_code)
        return []
    today = date.today()
    results = []
    for item in resp.json().get("items", []):
        created = date.fromisoformat(item["created_at"][:10])
        age_days = (today - created).days
        if age_days > days:
            continue
        results.append({
            "name": item["name"],
            "score": item["stargazers_count"] / max(age_days, 1),
            "source": "github",
        })
    return results


def _fetch_hn(days: int, limit: int) -> list[dict]:
    cutoff_ts = int(datetime(*(date.today() - timedelta(days=days)).timetuple()[:6],
                             tzinfo=timezone.utc).timestamp())
    try:
        resp = requests.get(
            "https://hn.algolia.com/api/v1/search",
            params={
                "tags": "story",
                "numericFilters": f"created_at_i>{cutoff_ts}",
                "hitsPerPage": limit,
            },
            timeout=_TIMEOUT,
        )
    except Exception as exc:
        logger.warning("HN fetch failed: %s", exc)
        return []
    if resp.status_code != 200:
        logger.warning("HN API error %s", resp.status_code)
        return []
    results = []
    for hit in resp.json().get("hits", []):
        title = hit.get("title") or ""
        points = hit.get("points") or 0
        if title:
            results.append({"name": title, "score": float(points), "source": "hn"})
    return results


def _fetch_reddit(days: int, limit: int) -> list[dict]:
    headers = {"User-Agent": "dnsexists/1.0"}
    results = []
    for sub in _SUBREDDITS:
        try:
            resp = requests.get(
                f"https://www.reddit.com/r/{sub}/top.json",
                params={"t": "week", "limit": limit},
                headers=headers,
                timeout=_TIMEOUT,
            )
        except Exception as exc:
            logger.warning("Reddit fetch failed (%s): %s", sub, exc)
            continue
        if resp.status_code != 200:
            logger.warning("Reddit API error %s (%s)", resp.status_code, sub)
            continue
        for child in resp.json().get("data", {}).get("children", []):
            data = child.get("data", {})
            title = data.get("title") or ""
            score = data.get("score") or 0
            if title:
                results.append({"name": title, "score": float(score), "source": "reddit"})
    return results


def _fetch_ph(days: int, limit: int) -> list[dict]:
    token = os.environ.get("PRODUCT_HUNT_TOKEN")
    if not token:
        logger.warning("PRODUCT_HUNT_TOKEN not set; skipping Product Hunt")
        return []
    query = """
    {
      posts(order: VOTES, first: %d) {
        edges { node { name votesCount } }
      }
    }
    """ % limit
    try:
        resp = requests.post(
            "https://api.producthunt.com/v2/api/graphql",
            json={"query": query},
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            timeout=_TIMEOUT,
        )
    except Exception as exc:
        logger.warning("Product Hunt fetch failed: %s", exc)
        return []
    if resp.status_code != 200:
        logger.warning("Product Hunt API error %s", resp.status_code)
        return []
    edges = resp.json().get("data", {}).get("posts", {}).get("edges", [])
    results = []
    for edge in edges:
        node = edge.get("node", {})
        name = node.get("name") or ""
        votes = node.get("votesCount") or 0
        if name:
            results.append({"name": name, "score": float(votes), "source": "producthunt"})
    return results


def _merge(entries: list[dict], weights: dict, limit: int) -> list[dict]:
    groups: dict[str, dict] = {}
    for entry in entries:
        key = _normalize(entry["name"])
        if not key:
            continue
        w = weights.get(entry["source"], 1.0)
        if key not in groups:
            groups[key] = {"name": key, "score": 0.0, "sources": set()}
        groups[key]["score"] += entry["score"] * w
        groups[key]["sources"].add(entry["source"])
    merged = []
    for g in groups.values():
        g["score"] *= len(g["sources"])
        g["sources"] = list(g["sources"])
        merged.append(g)
    merged.sort(key=lambda x: x["score"], reverse=True)
    return merged[:limit]


def fetch(args: dict) -> list[dict]:
    days = args.get("days", 7)
    limit = args.get("limit", 50)
    weights = args.get("weights", DEFAULT_WEIGHTS)
    all_entries = (
        _fetch_github(days=days, limit=limit)
        + _fetch_hn(days=days, limit=limit)
        + _fetch_reddit(days=days, limit=limit)
        + _fetch_ph(days=days, limit=limit)
    )
    return _merge(all_entries, weights, limit)


def select(candidates: list[dict]) -> list[str]:
    results = []
    for item in candidates:
        name = item["name"]
        if len(name) < 3 or len(name) > 30:
            continue
        if name.isdigit():
            continue
        if name:
            results.append(name)
    return results
