# Source: Andrej Karpathy LLM Wiki Architecture Concept

Date: 2026-11-03
Author: Andrej Karpathy / Community synthesis
Reference: https://gist.github.com/karpathy

## Core Principles
1. Compile-time Knowledge vs Runtime RAG:
   - RAG performs fuzzy retrieval at prompt time, incurring token cost and chunking noise.
   - LLM Wiki compiles, deduplicates, and synthesizes facts at ingest time into clean human-readable Markdown.
2. Three-layer Architecture:
   - raw/ (or sources/): Immutable source texts, transcripts, scrapes. Never edited by AI.
   - wiki/: AI-maintained knowledge base, cross-linked, structured with frontmatter.
   - index.md & log.md: Human and agent entry point, chronological audit trail.
3. Operations:
   - Ingest: Read raw sources, update or create wiki pages, append to log.
   - Query: Answer questions citing wiki pages with provenance back to raw sources.
   - Lint: Validate graph integrity, check broken [[links]], unindexed pages, orphan notes.
