"""
agent/brain.py — Claude-powered research intelligence.
Handles: query planning, source analysis, contradiction detection, report synthesis.
"""

from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import List, Optional
import anthropic
from rich.console import Console

from config import (
    EnvConfig, SearchQuery, ScrapedSource,
    KeyFinding, Contradiction, ResearchReport
)
from tools.vector_store import VectorStore

console = Console()
_client: Optional[anthropic.Anthropic] = None


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=EnvConfig.ANTHROPIC_API_KEY)
    return _client


# ── Step 1: Query Planning ────────────────────────────────────────────────

def plan_research_queries(topic: str) -> List[SearchQuery]:
    """
    Claude generates a smart set of search queries to thoroughly research a topic.
    Covers different angles: overview, technical, critique, recent news, data/stats.
    """
    depth_map = {"quick": 4, "standard": 6, "deep": EnvConfig.MAX_SEARCH_QUERIES}
    num_queries = depth_map.get(EnvConfig.RESEARCH_DEPTH, 8)

    prompt = f"""You are an expert research strategist. Plan a comprehensive research strategy for this topic.

TOPIC: {topic}
TARGET QUERIES: {num_queries}
DEPTH: {EnvConfig.RESEARCH_DEPTH}

Generate diverse search queries that together cover:
- General overview and definitions
- Technical or scientific details
- Recent developments (last 1-2 years)
- Criticisms, controversies, or limitations
- Statistics, data, and evidence
- Expert opinions and authoritative sources
- Comparisons and alternatives (if applicable)

Respond ONLY with a JSON array (no markdown):
[
  {{
    "query": "the exact search query string",
    "rationale": "why this query is needed",
    "angle": "overview|technical|recent|critique|data|expert|comparison",
    "priority": 1
  }}
]

Priority: 1 = most important. Number them 1 through {num_queries}.
Make queries specific and targeted — avoid vague one-word queries."""

    try:
        resp = get_client().messages.create(
            model="claude-opus-4-5",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.content[0].text.strip().replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)
        queries = [SearchQuery(**q) for q in data]
        console.print(f"  [green]✓[/green] Planned {len(queries)} search queries.")
        return queries
    except Exception as e:
        console.print(f"  [red]Query planning failed:[/red] {e}")
        return _fallback_queries(topic)


# ── Step 2: Source Credibility Scoring ───────────────────────────────────

def score_and_filter_sources(sources: List[ScrapedSource], topic: str) -> List[ScrapedSource]:
    """
    Claude reviews all sources and scores their relevance + credibility.
    Filters out low-quality or off-topic sources.
    """
    if not sources:
        return []

    source_summaries = "\n".join([
        f"[{i}] {s.domain} ({s.source_type}) — credibility: {s.credibility}/10\n"
        f"    Title: {s.title[:80]}\n"
        f"    Preview: {s.content[:200]}..."
        for i, s in enumerate(sources)
    ])

    prompt = f"""You are a research quality assessor. Rate these sources for the research topic.

TOPIC: {topic}

SOURCES:
{source_summaries}

For each source, assess:
1. Relevance to the topic (0-10)
2. Keep or discard (keep if relevance ≥ 5)

Respond ONLY with a JSON array:
[{{"index": 0, "relevance": 8, "keep": true}}, ...]"""

    try:
        resp = get_client().messages.create(
            model="claude-haiku-4-5-20251001",   # use fast model for filtering
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.content[0].text.strip().replace("```json", "").replace("```", "").strip()
        ratings = json.loads(raw)

        filtered = []
        for r in ratings:
            idx = r.get("index", -1)
            if r.get("keep") and 0 <= idx < len(sources):
                filtered.append(sources[idx])

        console.print(f"  [green]✓[/green] {len(filtered)}/{len(sources)} sources passed quality filter.")
        return filtered

    except Exception as e:
        console.print(f"  [yellow]Source filtering failed ({e}) — keeping all sources.[/yellow]")
        return sources


# ── Step 3: Key Finding Extraction ───────────────────────────────────────

def extract_key_findings(
    sources: List[ScrapedSource],
    topic: str,
    vector_store: VectorStore,
) -> List[KeyFinding]:
    """
    Claude reads all sources and extracts the most important findings,
    backed by specific evidence and citations.
    """
    console.print(f"  [dim]Extracting key findings from {len(sources)} sources...[/dim]")

    # Build source context (trim each to save tokens)
    source_context = "\n\n---\n\n".join([
        f"SOURCE [{i+1}]: {s.domain} ({s.source_type}, credibility: {s.credibility}/10)\n"
        f"URL: {s.url}\n"
        f"Title: {s.title}\n\n"
        f"{s.content[:EnvConfig.MAX_CONTENT_LENGTH]}"
        for i, s in enumerate(sources[:15])  # cap at 15 sources per call
    ])

    prompt = f"""You are a senior research analyst. Extract the most important findings from these sources.

RESEARCH TOPIC: {topic}

SOURCES:
{source_context}

Extract 8-12 key findings. Each finding should be:
- A specific, falsifiable claim (not vague)
- Backed by concrete evidence from the sources
- Categorized correctly

Respond ONLY with a JSON array (no markdown):
[
  {{
    "claim": "Specific factual claim or finding",
    "evidence": "The specific evidence or data from sources that supports this",
    "sources": ["url1", "url2"],
    "confidence": "high|medium|low",
    "category": "fact|opinion|data|trend"
  }}
]"""

    try:
        resp = get_client().messages.create(
            model="claude-opus-4-5",
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.content[0].text.strip().replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)
        findings = [KeyFinding(**f) for f in data]
        console.print(f"  [green]✓[/green] Extracted {len(findings)} key findings.")
        return findings
    except Exception as e:
        console.print(f"  [red]Finding extraction failed:[/red] {e}")
        return []


# ── Step 4: Contradiction Detection ──────────────────────────────────────

def detect_contradictions(
    sources: List[ScrapedSource],
    findings: List[KeyFinding],
    topic: str,
) -> List[Contradiction]:
    """
    Claude identifies where sources disagree and explains which is more credible.
    This is a unique differentiator — most research tools skip this.
    """
    if not EnvConfig.ENABLE_CONTRADICTIONS or len(sources) < 2:
        return []

    console.print("  [dim]Detecting contradictions across sources...[/dim]")

    findings_text = "\n".join([
        f"- [{f.confidence}] {f.claim} (sources: {', '.join(f.sources[:2])})"
        for f in findings
    ])

    source_snippets = "\n\n".join([
        f"[{s.domain}]: {s.content[:600]}"
        for s in sources[:10]
    ])

    prompt = f"""You are a fact-checker and research analyst. Identify contradictions between these sources.

TOPIC: {topic}

KEY FINDINGS:
{findings_text}

SOURCE CONTENT:
{source_snippets}

Find up to 5 genuine contradictions where sources make conflicting factual claims.
Skip minor wording differences — focus on real factual conflicts.

If no genuine contradictions exist, return an empty array.

Respond ONLY with a JSON array (no markdown):
[
  {{
    "topic": "What aspect they disagree on",
    "claim_a": "First claim",
    "source_a": "domain or URL of first source",
    "claim_b": "Conflicting claim",
    "source_b": "domain or URL of second source",
    "resolution": "Which is more likely correct and why, based on credibility and evidence"
  }}
]"""

    try:
        resp = get_client().messages.create(
            model="claude-opus-4-5",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.content[0].text.strip().replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)
        contradictions = [Contradiction(**c) for c in data]
        if contradictions:
            console.print(f"  [yellow]⚠[/yellow] Found {len(contradictions)} contradictions.")
        else:
            console.print("  [green]✓[/green] No major contradictions found.")
        return contradictions
    except Exception as e:
        console.print(f"  [yellow]Contradiction detection failed: {e}[/yellow]")
        return []


# ── Step 5: Report Synthesis ──────────────────────────────────────────────

def synthesize_report(
    topic: str,
    session_id: str,
    sources: List[ScrapedSource],
    findings: List[KeyFinding],
    contradictions: List[Contradiction],
    vector_store: VectorStore,
) -> ResearchReport:
    """
    Claude synthesizes everything into a structured, cited research report.
    The crown jewel of the agent — produces publication-quality output.
    """
    console.print("  [dim]Synthesizing final report...[/dim]")

    style_instructions = {
        "academic":   "Use formal academic language. Cite sources inline. Present multiple perspectives.",
        "journalist": "Write in clear journalistic prose. Lead with the most important finding. Use quotes.",
        "executive":  "Be concise and direct. Focus on implications and actionable insights. Use bullet points.",
        "simple":     "Write in plain language anyone can understand. Avoid jargon. Use examples.",
    }.get(EnvConfig.REPORT_STYLE, "Use clear professional language.")

    high_conf_findings = [f for f in findings if f.confidence == "high"]
    findings_text = "\n".join([
        f"- [{f.confidence.upper()}] {f.claim} | Evidence: {f.evidence[:150]}"
        for f in findings
    ])

    contradictions_text = (
        "\n".join([
            f"- {c.topic}: '{c.claim_a}' ({c.source_a}) vs '{c.claim_b}' ({c.source_b})"
            for c in contradictions
        ]) or "None identified."
    )

    source_domains = list({s.domain for s in sources})

    prompt = f"""You are a senior research analyst writing a comprehensive research report.

TOPIC: {topic}
STYLE: {style_instructions}
SOURCES USED: {', '.join(source_domains[:20])}

KEY FINDINGS:
{findings_text}

CONTRADICTIONS IDENTIFIED:
{contradictions_text}

Write a full, structured research report. Respond ONLY with a JSON object (no markdown):
{{
  "executive_summary": "3-4 paragraph summary of the most important findings and their significance",
  "sections": [
    {{
      "heading": "Section Title",
      "content": "Full section content with citations like [source.com]. Write at least 3-4 paragraphs per section."
    }}
  ],
  "conclusion": "2-3 paragraphs synthesizing the findings, implications, and open questions",
  "limitations": "What this research could not cover, gaps in sources, areas needing more study"
}}

Include 4-6 substantive sections. Each section should be 200-400 words.
Suggested sections: Background & Context, Key Findings, Evidence & Data, Controversies & Contradictions, Expert Perspectives, Implications & Future Outlook."""

    try:
        resp = get_client().messages.create(
            model="claude-opus-4-5",
            max_tokens=5000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.content[0].text.strip().replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)

        full_text = data["executive_summary"] + data["conclusion"] + \
                    " ".join(s["content"] for s in data.get("sections", []))
        word_count = len(full_text.split())

        return ResearchReport(
            session_id=session_id,
            topic=topic,
            executive_summary=data["executive_summary"],
            key_findings=findings,
            contradictions=contradictions,
            sections=data.get("sections", []),
            conclusion=data["conclusion"],
            sources_cited=sources,
            limitations=data.get("limitations", ""),
            generated_at=datetime.now(timezone.utc).isoformat(),
            word_count=word_count,
            source_count=len(sources),
        )

    except Exception as e:
        console.print(f"  [red]Report synthesis failed:[/red] {e}")
        return ResearchReport(
            session_id=session_id, topic=topic,
            executive_summary=f"Report synthesis error: {e}",
            key_findings=findings, contradictions=contradictions,
            sections=[], conclusion="", sources_cited=sources,
            limitations="Synthesis failed.", generated_at=datetime.now(timezone.utc).isoformat(),
        )


# ── Fallback queries ──────────────────────────────────────────────────────

def _fallback_queries(topic: str) -> List[SearchQuery]:
    return [
        SearchQuery(query=f"{topic} overview",          rationale="General overview",  angle="overview",   priority=1),
        SearchQuery(query=f"{topic} research findings", rationale="Research data",      angle="technical",  priority=2),
        SearchQuery(query=f"{topic} latest 2024 2025",  rationale="Recent developments",angle="recent",     priority=3),
        SearchQuery(query=f"{topic} criticism problems",rationale="Critical perspectives",angle="critique", priority=4),
        SearchQuery(query=f"{topic} statistics data",   rationale="Data and evidence",  angle="data",       priority=5),
    ]
