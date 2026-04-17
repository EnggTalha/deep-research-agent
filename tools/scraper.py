"""
tools/scraper.py — Extract clean article content from URLs.
Uses trafilatura (best-in-class article extractor) with BS4 fallback.
Caches results to avoid re-scraping.
"""

from __future__ import annotations
import hashlib
import json
import time
from datetime import datetime, timezone
from typing import List, Optional
from pathlib import Path
from urllib.parse import urlparse
from rich.console import Console

from config import EnvConfig, SearchResult, ScrapedSource, CACHE_DIR

console = Console()

# Domains to skip (paywalls, login walls, etc.)
SKIP_DOMAINS = {
    "twitter.com", "x.com", "facebook.com", "instagram.com",
    "linkedin.com", "tiktok.com", "youtube.com",
    "wsj.com", "ft.com", "bloomberg.com",    # paywalls
}


def scrape_sources(results: List[SearchResult]) -> List[ScrapedSource]:
    """Scrape content from search result URLs."""
    scraped: List[ScrapedSource] = []

    for r in results:
        domain = _get_domain(r.url)
        if domain in SKIP_DOMAINS:
            console.print(f"  [dim]Skipping {domain} (blocked)[/dim]")
            continue

        source = _scrape_url(r.url, r.title, r.source_type)
        if source and len(source.content) > 200:
            scraped.append(source)
            console.print(
                f"  [green]✓[/green] {domain} — {source.word_count} words "
                f"[dim]({source.source_type})[/dim]"
            )
        else:
            console.print(f"  [dim]✗ {domain} — too short or failed[/dim]")

        time.sleep(0.3)

    console.print(f"  [green]✓[/green] Scraped {len(scraped)} sources successfully.")
    return scraped


def _scrape_url(url: str, title: str, source_type: str) -> Optional[ScrapedSource]:
    """Try cache first, then live scrape."""
    cached = _load_cache(url)
    if cached:
        console.print(f"  [dim](cached)[/dim] {_get_domain(url)}")
        return cached

    source = _live_scrape(url, title, source_type)
    if source:
        _save_cache(url, source)
    return source


def _live_scrape(url: str, title: str, source_type: str) -> Optional[ScrapedSource]:
    """Scrape a single URL using trafilatura + BS4 fallback."""
    domain = _get_domain(url)

    # Try trafilatura first (best article extractor)
    content = _trafilatura_extract(url)

    # Fallback to requests + BS4
    if not content or len(content) < 200:
        content = _bs4_extract(url)

    if not content or len(content) < 100:
        return None

    # Trim to configured max length
    content = content[:EnvConfig.MAX_CONTENT_LENGTH * 3]  # keep more for embedding, trim later

    return ScrapedSource(
        url=url,
        title=title,
        content=content[:EnvConfig.MAX_CONTENT_LENGTH * 3],
        source_type=source_type,
        domain=domain,
        word_count=len(content.split()),
        scraped_at=datetime.now(timezone.utc).isoformat(),
        credibility=_estimate_credibility(domain, source_type),
    )


def _trafilatura_extract(url: str) -> Optional[str]:
    try:
        import trafilatura
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(
                downloaded,
                include_comments=False,
                include_tables=True,
                no_fallback=False,
            )
            return text
        return None
    except ImportError:
        return None
    except Exception:
        return None


def _bs4_extract(url: str) -> Optional[str]:
    try:
        import requests
        from bs4 import BeautifulSoup
        from fake_useragent import UserAgent

        headers = {"User-Agent": UserAgent().random}
        resp = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        if resp.status_code != 200:
            return None

        soup = BeautifulSoup(resp.content, "lxml")

        # Remove boilerplate
        for tag in soup(["script", "style", "nav", "footer", "header",
                          "aside", "advertisement", "iframe"]):
            tag.decompose()

        # Try article tags first
        for selector in ["article", "main", ".article-body", ".post-content",
                          ".entry-content", "#content"]:
            el = soup.select_one(selector)
            if el:
                text = el.get_text(separator="\n", strip=True)
                if len(text) > 300:
                    return text

        # Fallback: all paragraphs
        paragraphs = soup.find_all("p")
        text = "\n".join(p.get_text(strip=True) for p in paragraphs if len(p.get_text()) > 50)
        return text if len(text) > 200 else None

    except Exception:
        return None


def _estimate_credibility(domain: str, source_type: str) -> int:
    """Quick credibility estimate 1-10."""
    if source_type == "academic":   return 9
    if source_type == "official":   return 8
    if source_type == "news":
        trusted = ["bbc", "reuters", "apnews", "nytimes", "guardian", "nature", "science"]
        return 8 if any(t in domain for t in trusted) else 6
    if source_type == "forum":      return 4
    return 5   # blog / unknown


def _get_domain(url: str) -> str:
    try:
        return urlparse(url).netloc.replace("www.", "")
    except Exception:
        return url[:30]


# ── Cache ────────────────────────────────────────────────────────────────

def _cache_path(url: str) -> Path:
    key = hashlib.md5(url.encode()).hexdigest()[:16]
    return CACHE_DIR / f"{key}.json"


def _load_cache(url: str) -> Optional[ScrapedSource]:
    path = _cache_path(url)
    if not path.exists():
        return None
    try:
        with open(path) as f:
            return ScrapedSource(**json.load(f))
    except Exception:
        return None


def _save_cache(url: str, source: ScrapedSource) -> None:
    path = _cache_path(url)
    with open(path, "w") as f:
        json.dump(source.model_dump(), f, indent=2, default=str)
