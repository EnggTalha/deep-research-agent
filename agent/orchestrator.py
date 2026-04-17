"""
agent/orchestrator.py — Main agentic research loop.

Flow:
1. Claude plans search queries (diverse angles)
2. DuckDuckGo searches each query (free, no key)
3. Trafilatura scrapes + cleans article content
4. Cache deduplicates repeat URLs
5. FAISS vector index built over all content
6. Claude scores + filters sources by relevance
7. Claude extracts key findings with citations
8. Claude detects contradictions between sources
9. Claude synthesizes full structured report
10. Save Markdown + JSON reports
"""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from config import EnvConfig, ResearchSession
from tools.searcher import run_searches
from tools.scraper import scrape_sources
from tools.vector_store import VectorStore
from tools.reporter import print_terminal_summary, save_markdown_report, save_json_report
from agent.brain import (
    plan_research_queries,
    score_and_filter_sources,
    extract_key_findings,
    detect_contradictions,
    synthesize_report,
)

console = Console()


class DeepResearchAgent:
    """Autonomous deep research agent powered by Claude."""

    def research(self, topic: str) -> str:
        """
        Run a full research session on a topic.
        Returns path to the generated Markdown report.
        """
        session_id = str(uuid.uuid4())[:8]

        console.print(Panel.fit(
            f"[bold cyan]🔬 AI Deep Research Agent[/bold cyan]\n"
            f"Topic: [bold]{topic}[/bold]\n"
            f"Depth: {EnvConfig.RESEARCH_DEPTH} | "
            f"Style: {EnvConfig.REPORT_STYLE} | "
            f"Max queries: {EnvConfig.MAX_SEARCH_QUERIES}",
            border_style="cyan",
        ))

        session = ResearchSession(
            id=session_id,
            topic=topic,
            created_at=datetime.now(timezone.utc).isoformat(),
            status="searching",
        )

        # ── Step 1: Plan queries ────────────────────────────────────────
        console.print("\n[bold cyan]🗺️  Planning research strategy...[/bold cyan]")
        queries = plan_research_queries(topic)
        session.queries = queries

        console.print(f"\n  Queries planned:")
        for q in queries:
            console.print(f"  [{q.priority}] [dim]{q.query}[/dim]  ({q.angle})")

        # ── Step 2: Search ──────────────────────────────────────────────
        console.print("\n[bold cyan]🔍 Searching the web...[/bold cyan]")
        search_results = run_searches(queries)

        if not search_results:
            console.print("[red]No search results found. Check your internet connection.[/red]")
            return ""

        # ── Step 3: Scrape ──────────────────────────────────────────────
        session.status = "scraping"
        console.print(f"\n[bold cyan]📥 Scraping {len(search_results)} sources...[/bold cyan]")
        raw_sources = scrape_sources(search_results)

        if not raw_sources:
            console.print("[red]No sources could be scraped.[/red]")
            return ""

        # ── Step 4: Build vector index ──────────────────────────────────
        console.print("\n[bold cyan]🧠 Building semantic index...[/bold cyan]")
        vector_store = VectorStore()
        vector_store.build(raw_sources)

        # ── Step 5: Filter sources ──────────────────────────────────────
        session.status = "analyzing"
        console.print("\n[bold cyan]🔎 Scoring source relevance...[/bold cyan]")
        sources = score_and_filter_sources(raw_sources, topic)
        session.sources = sources

        # ── Step 6: Extract findings ────────────────────────────────────
        console.print("\n[bold cyan]🔍 Extracting key findings...[/bold cyan]")
        findings = extract_key_findings(sources, topic, vector_store)
        session.key_findings = findings

        # ── Step 7: Detect contradictions ───────────────────────────────
        console.print("\n[bold cyan]⚖️  Checking for contradictions...[/bold cyan]")
        contradictions = detect_contradictions(sources, findings, topic)
        session.contradictions = contradictions

        # ── Step 8: Synthesize report ───────────────────────────────────
        session.status = "synthesizing"
        console.print("\n[bold cyan]✍️  Synthesizing research report...[/bold cyan]")
        report = synthesize_report(
            topic, session_id, sources, findings, contradictions, vector_store
        )

        # ── Step 9: Save + display ──────────────────────────────────────
        session.status = "complete"
        print_terminal_summary(report)

        md_path   = save_markdown_report(report)
        json_path = save_json_report(report)

        console.print(f"\n[bold green]✓ Research complete![/bold green]")
        console.print(f"  📄 Report:  [dim]{md_path}[/dim]")
        console.print(f"  📦 JSON:    [dim]{json_path}[/dim]")
        console.print(
            f"  📊 Stats:   {report.source_count} sources | "
            f"{report.word_count:,} words | "
            f"{len(report.key_findings)} findings | "
            f"{len(report.contradictions)} contradictions\n"
        )

        return str(md_path)
