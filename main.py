"""
main.py — CLI entry point for the AI Deep Research Agent.

Usage:
  python main.py "impact of AI on software engineering jobs"
  python main.py "quantum computing applications" --depth deep --style academic
  python main.py "climate change solutions" --depth quick --style executive
  python main.py "LLM hallucination problem" --queries 12 --no-contradictions
"""

import argparse
import sys
from rich.console import Console
from config import EnvConfig

console = Console()


def validate_env() -> bool:
    if not EnvConfig.ANTHROPIC_API_KEY:
        console.print("[bold red]Error:[/bold red] ANTHROPIC_API_KEY is not set.")
        console.print("Copy [dim].env.example[/dim] → [dim].env[/dim] and fill in your key.")
        return False
    return True


def main():
    parser = argparse.ArgumentParser(
        description="AI Deep Research Agent — powered by Claude",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py "impact of AI on jobs"
  python main.py "quantum computing" --depth deep --style academic
  python main.py "climate tech" --depth quick --style executive
  python main.py "LLM safety" --queries 12 --style journalist
        """,
    )
    parser.add_argument("topic", nargs="?", help="Research topic or question")
    parser.add_argument(
        "--depth", choices=["quick", "standard", "deep"], default=None,
        help="Research depth: quick (4 queries), standard (6), deep (8+)"
    )
    parser.add_argument(
        "--style", choices=["academic", "journalist", "executive", "simple"], default=None,
        help="Report writing style"
    )
    parser.add_argument(
        "--queries", type=int, default=None,
        help="Max number of search queries (overrides depth setting)"
    )
    parser.add_argument(
        "--no-contradictions", action="store_true",
        help="Skip contradiction detection (faster)"
    )
    parser.add_argument(
        "--no-vectors", action="store_true",
        help="Skip FAISS vector indexing (no OpenAI key needed)"
    )
    parser.add_argument(
        "--format", choices=["markdown", "json", "both"], default=None,
        help="Output format"
    )
    args = parser.parse_args()

    if not args.topic:
        parser.print_help()
        console.print("\n[yellow]Please provide a research topic.[/yellow]")
        console.print('Example: python main.py "impact of AI on software jobs"')
        sys.exit(1)

    # Apply CLI overrides
    if args.depth:
        EnvConfig.RESEARCH_DEPTH = args.depth
    if args.style:
        EnvConfig.REPORT_STYLE = args.style
    if args.queries:
        EnvConfig.MAX_SEARCH_QUERIES = args.queries
    if args.no_contradictions:
        EnvConfig.ENABLE_CONTRADICTIONS = False
    if args.no_vectors:
        EnvConfig.ENABLE_VECTOR_SEARCH = False
    if args.format:
        EnvConfig.OUTPUT_FORMAT = args.format

    if not validate_env():
        sys.exit(1)

    from agent.orchestrator import DeepResearchAgent
    agent = DeepResearchAgent()
    agent.research(args.topic)


if __name__ == "__main__":
    main()
