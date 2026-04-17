"""
tools/searcher.py — Web search using DuckDuckGo (free, no API key).
Optional: Tavily API for higher-quality academic/news results.
"""

from __future__ import annotations
import time
from typing import List
from rich.console import Console

from config import EnvConfig, SearchQuery, SearchResult

console = Console()


def run_searches(queries: List[SearchQuery]) -> List[SearchResult]:
    """Run all search queries and return deduplicated results."""
    all_results: List[SearchResult] = []
    seen_urls: set[str] = set()

    for q in sorted(queries, key=lambda x: x.priority):
        console.print(f"  [dim]🔍 Searching: {q.query[:70]}[/dim]")
        results = _search_single(q)

        for r in results:
            if r.url not in seen_urls:
                seen_urls.add(r.url)
                all_results.append(r)

        time.sleep(0.5)   # polite rate limiting

    console.print(f"  [green]✓[/green] {len(all_results)} unique URLs found across {len(queries)} queries.")
    return all_results


def _search_single(query: SearchQuery) -> List[SearchResult]:
    """Try Tavily first (if key set), fall back to DuckDuckGo."""
    if EnvConfig.TAVILY_API_KEY:
        results = _tavily_search(query)
        if results:
            return results

    return _ddg_search(query)


def _ddg_search(query: SearchQuery) -> List[SearchResult]:
    """DuckDuckGo search — completely free, no API key needed."""
    try:
        from duckduckgo_search import DDGS

        results = []
        with DDGS() as ddgs:
            raw = ddgs.text(
                query.query,
                max_results=EnvConfig.MAX_SOURCES_PER_QUERY,
                safesearch="moderate",
            )
            for r in raw:
                results.append(SearchResult(
                    url=r.get("href", ""),
                    title=r.get("title", ""),
                    snippet=r.get("body", "")[:300],
                    source_type=_classify_source(r.get("href", "")),
                    query=query.query,
                ))
        return results

    except ImportError:
        console.print("  [yellow]duckduckgo-search not installed. Using mock results.[/yellow]")
        return _mock_results(query)
    except Exception as e:
        console.print(f"  [yellow]DDG search error: {e} — using mock.[/yellow]")
        return _mock_results(query)


def _tavily_search(query: SearchQuery) -> List[SearchResult]:
    """Tavily API search — higher quality, free tier available."""
    try:
        import requests
        resp = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": EnvConfig.TAVILY_API_KEY,
                "query": query.query,
                "max_results": EnvConfig.MAX_SOURCES_PER_QUERY,
                "search_depth": "advanced",
                "include_answer": False,
            },
            timeout=15,
        )
        if resp.status_code != 200:
            return []

        data = resp.json()
        results = []
        for r in data.get("results", []):
            results.append(SearchResult(
                url=r.get("url", ""),
                title=r.get("title", ""),
                snippet=r.get("content", "")[:300],
                source_type=_classify_source(r.get("url", "")),
                query=query.query,
            ))
        return results

    except Exception as e:
        console.print(f"  [yellow]Tavily error: {e}[/yellow]")
        return []


def _classify_source(url: str) -> str:
    url = url.lower()
    if any(x in url for x in [".edu", "arxiv", "pubmed", "scholar", "researchgate", "jstor"]):
        return "academic"
    if any(x in url for x in ["bbc", "reuters", "apnews", "nytimes", "guardian", "techcrunch"]):
        return "news"
    if any(x in url for x in [".gov", "who.int", "un.org", "worldbank"]):
        return "official"
    if any(x in url for x in ["reddit", "stackoverflow", "quora", "hackernews", "news.ycombinator"]):
        return "forum"
    return "blog"


def _mock_results(query: SearchQuery) -> List[SearchResult]:
    """Return mock results for testing without internet access."""
    return [
        SearchResult(
            url=f"https://example-{i}.com/article-about-{query.query[:20].replace(' ','-')}",
            title=f"Research article on {query.query[:40]} — Part {i}",
            snippet=f"This article discusses key aspects of {query.query}. "
                    f"Research shows significant developments in this area with multiple perspectives...",
            source_type=["academic", "news", "blog", "official"][i % 4],
            query=query.query,
        )
        for i in range(1, 4)
    ]
