"""
tools/vector_store.py — FAISS-based semantic search across scraped sources.
Embeds source content with OpenAI text-embedding-3-small (cheap + fast).
Enables finding related content across sources for synthesis.
"""

from __future__ import annotations
import json
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional
from rich.console import Console

from config import EnvConfig, ScrapedSource

console = Console()

CHUNK_SIZE   = 500    # words per chunk
CHUNK_OVERLAP = 50    # overlap between chunks


class VectorStore:
    """In-memory FAISS index over source content chunks."""

    def __init__(self):
        self.chunks:     List[str]          = []
        self.metadata:   List[dict]         = []
        self.embeddings: Optional[np.ndarray] = None
        self.index       = None
        self._ready      = False

    def build(self, sources: List[ScrapedSource]) -> None:
        """Chunk all sources and build FAISS index."""
        if not EnvConfig.ENABLE_VECTOR_SEARCH:
            console.print("  [dim]Vector search disabled.[/dim]")
            return

        if not EnvConfig.OPENAI_API_KEY:
            console.print("  [dim]No OpenAI key — vector search skipped.[/dim]")
            return

        console.print("  [dim]Building vector index...[/dim]")

        self.chunks   = []
        self.metadata = []

        for source in sources:
            for chunk, meta in _chunk_source(source):
                self.chunks.append(chunk)
                self.metadata.append(meta)

        if not self.chunks:
            return

        try:
            embeddings = _embed_texts(self.chunks)
            if embeddings is None:
                return

            import faiss
            self.embeddings = np.array(embeddings, dtype=np.float32)
            # Normalize for cosine similarity
            faiss.normalize_L2(self.embeddings)

            dim = self.embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dim)   # inner product = cosine on normalized vecs
            self.index.add(self.embeddings)
            self._ready = True

            console.print(f"  [green]✓[/green] Vector index built: {len(self.chunks)} chunks from {len(sources)} sources.")

        except ImportError:
            console.print("  [yellow]faiss-cpu not installed — skipping vector search.[/yellow]")
        except Exception as e:
            console.print(f"  [yellow]Vector index error: {e}[/yellow]")

    def search(self, query: str, k: int = 5) -> List[Tuple[str, dict, float]]:
        """
        Semantic search over source chunks.
        Returns list of (chunk_text, metadata, score).
        """
        if not self._ready or not self.index:
            return []

        try:
            import faiss
            query_emb = _embed_texts([query])
            if query_emb is None:
                return []

            q = np.array(query_emb, dtype=np.float32)
            faiss.normalize_L2(q)

            scores, indices = self.index.search(q, k)
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx >= 0 and idx < len(self.chunks):
                    results.append((self.chunks[idx], self.metadata[idx], float(score)))
            return results

        except Exception as e:
            console.print(f"  [yellow]Vector search error: {e}[/yellow]")
            return []

    def find_related(self, claim: str, k: int = 3) -> str:
        """Find chunks related to a claim. Returns formatted context string."""
        results = self.search(claim, k=k)
        if not results:
            return ""
        parts = []
        for text, meta, score in results:
            parts.append(f"[Source: {meta.get('domain', '?')} | Score: {score:.2f}]\n{text}")
        return "\n\n".join(parts)


# ── Chunking ─────────────────────────────────────────────────────────────

def _chunk_source(source: ScrapedSource) -> List[Tuple[str, dict]]:
    """Split a source into overlapping word chunks."""
    words = source.content.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk_words = words[i : i + CHUNK_SIZE]
        chunk_text  = " ".join(chunk_words)
        chunks.append((
            chunk_text,
            {
                "url":         source.url,
                "domain":      source.domain,
                "title":       source.title,
                "source_type": source.source_type,
                "credibility": source.credibility,
                "chunk_idx":   len(chunks),
            }
        ))
        i += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


# ── Embeddings ────────────────────────────────────────────────────────────

def _embed_texts(texts: List[str]) -> Optional[List[List[float]]]:
    """Embed a list of texts using OpenAI text-embedding-3-small."""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=EnvConfig.OPENAI_API_KEY)

        # Batch in groups of 100
        all_embeddings = []
        for i in range(0, len(texts), 100):
            batch = texts[i : i + 100]
            # Trim each text to ~8000 chars (token limit)
            batch = [t[:8000] for t in batch]
            resp = client.embeddings.create(
                model="text-embedding-3-small",
                input=batch,
            )
            all_embeddings.extend([item.embedding for item in resp.data])

        return all_embeddings

    except ImportError:
        return None
    except Exception as e:
        console.print(f"  [yellow]Embedding error: {e}[/yellow]")
        return None
