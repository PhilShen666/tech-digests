#!/usr/bin/env python3
"""
Fetch AI/RecSys items from RSS feeds and arXiv.

Usage:
    python fetch_items.py --since YYYY-MM-DD --until YYYY-MM-DD [--sources a,b,c]

Prints a JSON array to stdout. Errors per source go to stderr.

Note: affiliations are not extracted here — arXiv does not expose them in any
machine-readable feed or abstract page. Claude extracts them from the HTML
rendering when processing spotlight items.
"""
from __future__ import annotations

import argparse
import json
import sys
import re
from datetime import datetime, timezone, timedelta
import threading
from typing import Optional

import feedparser
import httpx

# Make sources importable when script is run directly
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from sources import FEEDS, ARXIV_CATEGORIES

ARXIV_MAX_RESULTS = 50
HTTP_TIMEOUT = 15


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------

def _to_utc(struct_time) -> Optional[datetime]:
    if struct_time is None:
        return None
    try:
        return datetime(*struct_time[:6], tzinfo=timezone.utc)
    except Exception:
        return None


def _date_window(since_str: str, until_str: str) -> tuple:
    since = datetime.fromisoformat(since_str).replace(tzinfo=timezone.utc)
    until = datetime.fromisoformat(until_str).replace(tzinfo=timezone.utc) + timedelta(days=1) - timedelta(seconds=1)
    return since, until


# ---------------------------------------------------------------------------
# RSS fetcher
# ---------------------------------------------------------------------------

def _fetch_rss(name: str, url: str, since: datetime, until: datetime) -> list:
    feed = feedparser.parse(url)
    items = []
    for entry in feed.entries:
        pub = _to_utc(getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None))
        if pub is None or not (since <= pub <= until):
            continue
        items.append({
            "source": name,
            "title": entry.get("title", "").strip(),
            "url": entry.get("link", ""),
            "published": pub.isoformat(),
            "summary": entry.get("summary", "").strip(),
            "authors": [],
        })
    return items


# ---------------------------------------------------------------------------
# arXiv fetcher
# ---------------------------------------------------------------------------

def _arxiv_date(dt: datetime) -> str:
    return dt.strftime("%Y%m%d%H%M%S")


def _fetch_arxiv(name: str, category: str, since: datetime, until: datetime) -> list:
    query = (
        f"https://export.arxiv.org/api/query"
        f"?search_query=cat:{category}+AND+submittedDate:[{_arxiv_date(since)}+TO+{_arxiv_date(until)}]"
        f"&sortBy=submittedDate&sortOrder=descending&max_results={ARXIV_MAX_RESULTS}"
    )
    resp = httpx.get(query, timeout=HTTP_TIMEOUT, follow_redirects=True,
                     headers={"User-Agent": "tech-digest-skill/1.0"})
    resp.raise_for_status()
    feed = feedparser.parse(resp.text)

    items = []
    lock = threading.Lock()

    def process(entry):
        pub = _to_utc(getattr(entry, "published_parsed", None))
        if pub is None or not (since <= pub <= until):
            return
        authors = [a.get("name", "") for a in getattr(entry, "authors", [])]
        item = {
            "source": name,
            "title": entry.get("title", "").strip().replace("\n", " "),
            "url": entry.get("link", ""),
            "published": pub.isoformat(),
            "summary": entry.get("summary", "").strip(),
            "authors": authors,
        }
        with lock:
            items.append(item)

    threads = [threading.Thread(target=process, args=(e,)) for e in feed.entries]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    return items


# ---------------------------------------------------------------------------
# Dedup
# ---------------------------------------------------------------------------

def _normalize_title(t: str) -> str:
    return re.sub(r"\s+", " ", t.lower().strip())


def _dedup(items: list) -> list:
    seen_urls: set = set()
    seen_titles: set = set()
    out = []
    # Prefer original sources over HN aggregator
    items = sorted(items, key=lambda x: (x["source"] == "hackernews", x["source"]))
    for item in items:
        url = item["url"]
        title_key = _normalize_title(item["title"])
        if url in seen_urls or title_key in seen_titles:
            continue
        seen_urls.add(url)
        seen_titles.add(title_key)
        out.append(item)
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def fetch_all(since: datetime, until: datetime, sources: Optional[list] = None) -> list:
    all_items = []

    for name, url in FEEDS.items():
        if sources and name not in sources:
            continue
        try:
            all_items.extend(_fetch_rss(name, url, since, until))
        except Exception as e:
            print(f"[feed error] {name}: {type(e).__name__}: {e}", file=sys.stderr)

    for name, category in ARXIV_CATEGORIES.items():
        if sources and name not in sources:
            continue
        try:
            all_items.extend(_fetch_arxiv(name, category, since, until))
        except Exception as e:
            print(f"[arxiv error] {name}: {type(e).__name__}: {e}", file=sys.stderr)

    all_items = _dedup(all_items)
    all_items.sort(key=lambda x: x["published"], reverse=True)
    return all_items


def main():
    parser = argparse.ArgumentParser(description="Fetch AI/RecSys digest items.")
    parser.add_argument("--since", required=True, help="Start date YYYY-MM-DD (inclusive)")
    parser.add_argument("--until", required=True, help="End date YYYY-MM-DD (inclusive)")
    parser.add_argument("--sources", default=None,
                        help="Comma-separated source names; omit for all")
    args = parser.parse_args()

    since, until = _date_window(args.since, args.until)
    source_list = [s.strip() for s in args.sources.split(",")] if args.sources else None

    items = fetch_all(since, until, source_list)
    print(json.dumps(items, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
