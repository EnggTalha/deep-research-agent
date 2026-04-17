# 🔬 AI Deep Research Agent

> Give it any topic. The agent autonomously searches the web, reads articles and papers, finds contradictions between sources, and synthesizes a structured research report with citations — in minutes.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Claude](https://img.shields.io/badge/Powered%20by-Claude%20Opus-blueviolet?logo=anthropic)
![DuckDuckGo](https://img.shields.io/badge/Search-DuckDuckGo%20(free)-orange)
![FAISS](https://img.shields.io/badge/Vector%20Search-FAISS-green)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 📸 Demo

```
╭──────────────────────────────────────────────────────────────╮
│  🔬 AI Deep Research Agent                                   │
│  Topic: Impact of AI on software engineering jobs            │
│  Depth: deep | Style: academic | Max queries: 8              │
╰──────────────────────────────────────────────────────────────╯

🗺️  Planning research strategy...
  ✓ Planned 8 search queries.

  Queries planned:
  [1] AI impact software developer employment 2024       (overview)
  [2] LLM code generation productivity research study    (technical)
  [3] GitHub Copilot developer job displacement study    (data)
  [4] software engineering jobs AI automation risk       (critique)
  [5] AI programming tools adoption statistics           (data)
  [6] future of software development AI agents 2025     (recent)
  [7] developers opinion AI tools job security survey    (expert)
  [8] AI replacing programmers counterarguments          (critique)

🔍 Searching the web...
  ✓ 31 unique URLs found across 8 queries.

📥 Scraping 31 sources...
  ✓ arxiv.org — 4,821 words (academic)
  ✓ techcrunch.com — 1,203 words (news)
  ✓ stackoverflow.blog — 2,100 words (blog)
  ✓ mckinsey.com — 3,400 words (official)
  ... (18 more)
  ✓ Scraped 22 sources successfully.

🧠 Building semantic index...
  ✓ Vector index built: 187 chunks from 22 sources.

🔎 Scoring source relevance...
  ✓ 17/22 sources passed quality filter.

🔍 Extracting key findings...
  ✓ Extracted 11 key findings.

⚖️  Checking for contradictions...
  ⚠ Found 3 contradictions.

✍️  Synthesizing research report...

Research Complete
Topic: Impact of AI on software engineering jobs
Sources: 17 | Words: 4,821 | Findings: 11 | Contradictions: 3

┌─────┬─────────────┬────────────────────────────────────────────────────────────────────┐
│Conf │ Category    │ Finding                                                            │
├─────┼─────────────┼────────────────────────────────────────────────────────────────────┤
│ 🟢  │ 📊 data     │ GitHub Copilot users complete coding tasks 55% faster on average   │
│ 🟢  │ 📌 fact     │ McKinsey estimates 25% of software tasks could be automated by 2030│
│ 🟡  │ 📈 trend    │ Demand for AI-specialised engineers grew 40% YoY in 2024           │
│ 🟡  │ 💭 opinion  │ Most developers view AI as an augmentation tool, not a replacement │
│ 🔴  │ 📊 data     │ Stack Overflow survey: 62% of devs use AI tools daily              │
└─────┴─────────────┴────────────────────────────────────────────────────────────────────┘

⚠️  Contradictions Found
  ⚠️  Job displacement timeline
     A: AI will displace 30% of dev jobs by 2030 [goldman-sachs.com]
     B: Software engineering demand will grow 25% by 2030 [bls.gov]
     → BLS data is more methodologically rigorous; Goldman may conflate...

✓ Research complete!
  📄 Report:  data/reports/Impact_of_AI_on_software_20240418.md
  📦 JSON:    data/reports/Impact_of_AI_on_software_20240418.json
  📊 Stats:   17 sources | 4,821 words | 11 findings | 3 contradictions
```

---

## 🧠 How It Works

```
┌──────────────┐   ┌──────────────┐   ┌──────────────────────────┐
│  1. PLAN     │──▶│  2. SEARCH   │──▶│  3. SCRAPE               │
│              │   │              │   │                          │
│  Claude      │   │  DuckDuckGo  │   │  Trafilatura extracts    │
│  generates   │   │  (free, no   │   │  clean article text      │
│  8 targeted  │   │  API key)    │   │  BS4 fallback            │
│  queries     │   │  + Tavily    │   │  URL cache to avoid      │
│  by angle    │   │  (optional)  │   │  re-scraping             │
└──────────────┘   └──────────────┘   └──────────────────────────┘
                                                  │
                                                  ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────────────────┐
│  7. REPORT   │◀──│  6. DETECT   │◀──│  4. INDEX + FILTER       │
│              │   │              │   │                          │
│  Claude      │   │  Claude      │   │  FAISS vector index      │
│  synthesizes │   │  finds where │   │  OpenAI embeddings       │
│  structured  │   │  sources     │   │  Claude scores source    │
│  report with │   │  disagree    │   │  relevance 0-10          │
│  citations   │   │  + resolves  │   │  Filter low-quality      │
└──────────────┘   └──────────────┘   └──────────────────────────┘
                                                  │
                         ┌────────────────────────┘
                         ▼
               ┌──────────────────┐
               │  5. EXTRACT      │
               │                  │
               │  Claude finds    │
               │  key findings    │
               │  with citations  │
               │  confidence tags │
               └──────────────────┘
```

### What makes this different

| Feature | Most research tools | This agent |
|---|---|---|
| Source variety | Google top 5 | 8 angles × 5 sources = 40 URLs |
| Content extraction | Snippets only | Full article text via Trafilatura |
| Contradiction detection | ❌ | ✅ Claude finds + resolves conflicts |
| Semantic search | ❌ | ✅ FAISS over all content |
| Citation tracking | ❌ | ✅ Every claim linked to source |
| Source credibility | ❌ | ✅ Scored 1-10 per domain |
| Writing styles | One | Academic / Journalist / Executive / Simple |

---

## ✨ Features

| Feature | Details |
|---|---|
| 🗺️ Smart query planning | Claude generates 4–12 targeted queries across different angles |
| 🔍 Free search | DuckDuckGo — no API key needed |
| 📥 Full content extraction | Trafilatura reads full article text, not just snippets |
| 🗃️ Source caching | Scraped content cached — re-runs are instant |
| 🧠 Semantic search | FAISS + OpenAI embeddings for cross-source retrieval |
| 🔎 Quality filtering | Claude scores every source for relevance before using it |
| ⚖️ Contradiction detection | Finds where sources disagree and explains which is right |
| 📊 Confidence tagging | Every finding labeled high/medium/low confidence |
| ✍️ 4 writing styles | Academic, journalist, executive summary, or plain English |
| 📄 Full citations | Every claim linked to source URL with credibility score |

---

## 🗂️ Project Structure

```
deep-research-agent/
├── main.py                      # CLI entry point
├── config.py                    # Config, env vars, Pydantic models
├── requirements.txt
├── .env.example
│
├── agent/
│   ├── brain.py                 # Claude: query planning, analysis, synthesis
│   └── orchestrator.py          # Main research loop
│
├── tools/
│   ├── searcher.py              # DuckDuckGo + optional Tavily search
│   ├── scraper.py               # Trafilatura + BS4 content extractor + cache
│   ├── vector_store.py          # FAISS semantic index over all sources
│   └── reporter.py              # Terminal summary + Markdown/JSON reports
│
└── data/
    ├── research/                # Research session metadata
    ├── reports/                 # Generated Markdown + JSON reports
    └── cache/                   # Scraped URL content cache
```

---

## 🚀 Quickstart

### 1. Clone & install

```bash
git clone https://github.com/yourusername/ai-deep-research-agent.git
cd ai-deep-research-agent

python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Add ANTHROPIC_API_KEY (required)
# Add OPENAI_API_KEY (optional — for FAISS vector search)
```

### 3. Run your first research

```bash
python main.py "impact of AI on software engineering jobs"
```

### 4. Customize depth and style

```bash
# Quick executive summary
python main.py "quantum computing" --depth quick --style executive

# Deep academic research
python main.py "mRNA vaccine safety" --depth deep --style academic

# Journalist style, no vector search needed
python main.py "climate change tech" --style journalist --no-vectors
```

---

## ⚙️ CLI Reference

```
python main.py TOPIC [OPTIONS]

Arguments:
  TOPIC              Research topic or question (wrap in quotes)

Options:
  --depth LEVEL      quick | standard | deep  (default: deep)
                     quick=4 queries, standard=6, deep=8+
  --style STYLE      academic | journalist | executive | simple
  --queries INT      Exact number of search queries to run
  --no-contradictions  Skip contradiction detection (faster)
  --no-vectors       Skip FAISS indexing (no OpenAI key needed)
  --format FORMAT    markdown | json | both

Examples:
  python main.py "AI safety alignment problem"
  python main.py "Pakistan tech startup ecosystem" --depth standard --style journalist
  python main.py "intermittent fasting research" --depth deep --style academic
  python main.py "GPT-5 capabilities" --depth quick --no-vectors
```

---

## 📄 Sample Report Output

Reports are saved as clean Markdown with this structure:

```
# Research Report: Impact of AI on Software Engineering Jobs

Generated: April 18, 2026 | Sources: 17 | Words: 4,821 | Findings: 11

## 📋 Executive Summary
[3-4 paragraphs...]

## Background & Context
[Full section with inline citations...]

## Key Findings
[Full section...]

## Evidence & Data
[Full section...]

## Controversies & Contradictions
[Full section with source comparison...]

## Expert Perspectives
[Full section...]

## Implications & Future Outlook
[Full section...]

## ⚠️ Contradictions Found
[Detailed conflict analysis...]

## 🎯 Conclusion
[2-3 paragraphs...]

## 📚 Sources
[All 17 sources with URLs and credibility scores...]
```

---

## 🔑 API Keys & Cost

| Service | Used For | Cost |
|---|---|---|
| Anthropic Claude | Query planning, analysis, synthesis | ~$0.20–0.80 per research session |
| DuckDuckGo | Web search | Free — no key needed |
| OpenAI (optional) | FAISS embeddings | ~$0.01 per session |
| Tavily (optional) | Higher quality search | Free tier available |

**Estimated cost per deep research session:** ~$0.30–1.00

---

## 🤝 Contributing

Ideas welcome:

- [ ] arXiv / PubMed academic paper search
- [ ] PDF reading support
- [ ] Export to Notion / Google Docs
- [ ] Interactive Q&A mode after research
- [ ] Multi-language research support
- [ ] Research comparison mode (two topics side-by-side)

---

## 📄 License

MIT — see [LICENSE](LICENSE)

---

## 🙋 Author

Built by [EnggTalha](https://github.com/EnggTalha)

> ⭐ Star this repo if it saved you hours of research!
