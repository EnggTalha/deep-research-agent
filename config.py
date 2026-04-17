"""
config.py — Central config and data models for the Deep Research Agent.
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# ── Paths ───────────────────────────────────────────────────────────────
BASE_DIR      = Path(__file__).parent
DATA_DIR      = BASE_DIR / "data"
RESEARCH_DIR  = DATA_DIR / "research"
REPORTS_DIR   = DATA_DIR / "reports"
CACHE_DIR     = DATA_DIR / "cache"
LOG_DIR       = BASE_DIR / "logs"

for d in [RESEARCH_DIR, REPORTS_DIR, CACHE_DIR, LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# ── Env ─────────────────────────────────────────────────────────────────
class EnvConfig:
    ANTHROPIC_API_KEY:     str  = os.getenv("ANTHROPIC_API_KEY", "")
    OPENAI_API_KEY:        str  = os.getenv("OPENAI_API_KEY", "")
    TAVILY_API_KEY:        str  = os.getenv("TAVILY_API_KEY", "")
    MAX_SEARCH_QUERIES:    int  = int(os.getenv("MAX_SEARCH_QUERIES", "8"))
    MAX_SOURCES_PER_QUERY: int  = int(os.getenv("MAX_SOURCES_PER_QUERY", "5"))
    MAX_CONTENT_LENGTH:    int  = int(os.getenv("MAX_CONTENT_LENGTH", "3000"))
    RESEARCH_DEPTH:        str  = os.getenv("RESEARCH_DEPTH", "deep")
    ENABLE_CONTRADICTIONS: bool = os.getenv("ENABLE_CONTRADICTION_CHECK", "true").lower() == "true"
    ENABLE_VECTOR_SEARCH:  bool = os.getenv("ENABLE_VECTOR_SEARCH", "true").lower() == "true"
    OUTPUT_FORMAT:         str  = os.getenv("OUTPUT_FORMAT", "markdown")
    REPORT_STYLE:          str  = os.getenv("REPORT_STYLE", "academic")


# ── Data Models ──────────────────────────────────────────────────────────

class SearchQuery(BaseModel):
    query:     str
    rationale: str       # why this query is needed
    angle:     str       # "overview" | "technical" | "critique" | "recent" | "data"
    priority:  int       # 1 = highest


class SearchResult(BaseModel):
    url:         str
    title:       str
    snippet:     str
    source_type: str     # "news" | "academic" | "blog" | "official" | "forum"
    query:       str     # which query produced this result


class ScrapedSource(BaseModel):
    url:         str
    title:       str
    content:     str
    source_type: str
    domain:      str
    word_count:  int
    scraped_at:  str
    credibility: int     # 1–10 estimated by Claude


class KeyFinding(BaseModel):
    claim:       str
    evidence:    str
    sources:     List[str]      # URLs
    confidence:  str            # "high" | "medium" | "low"
    category:    str            # "fact" | "opinion" | "data" | "trend"


class Contradiction(BaseModel):
    topic:       str
    claim_a:     str
    source_a:    str
    claim_b:     str
    source_b:    str
    resolution:  str            # Claude's analysis of which is more credible


class ResearchSession(BaseModel):
    id:              str
    topic:           str
    queries:         List[SearchQuery]   = Field(default_factory=list)
    sources:         List[ScrapedSource] = Field(default_factory=list)
    key_findings:    List[KeyFinding]    = Field(default_factory=list)
    contradictions:  List[Contradiction] = Field(default_factory=list)
    status:          str = "pending"    # pending | searching | scraping | analyzing | complete
    created_at:      str = ""


class ResearchReport(BaseModel):
    session_id:       str
    topic:            str
    executive_summary: str
    key_findings:     List[KeyFinding]
    contradictions:   List[Contradiction]
    sections:         List[Dict]         # [{"heading": str, "content": str}]
    conclusion:       str
    sources_cited:    List[ScrapedSource]
    limitations:      str
    generated_at:     str
    word_count:       int = 0
    source_count:     int = 0
