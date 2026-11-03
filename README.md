# Autonomous LLM Wiki: Fast FTS5, 3-Tier LOD & Self-Healing Knowledge Engine

An autonomous, compile-time personal AI knowledge base inspired by Andrej Karpathy's architecture. Built with **Zero External Dependencies** using Python 3.9+ standard library.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.9+](https://img.shields.io/badge/Python-3.9%2B-brightgreen.svg)](https://www.python.org/)
[![Protocol: MCP](https://img.shields.io/badge/MCP-2024--11--05-orange.svg)](https://modelcontextprotocol.io/)

---

## 💡 Why This Project?

Traditional RAG (Retrieval-Augmented Generation) suffers from query-time hallucination, chunk-fragmentation, and heavy vector DB bloat. 

Following Andrej Karpathy's thesis:
> *"Obsidian is the IDE, the LLM is the programmer, and the Wiki is the codebase."*

This repository implements a **compile-time knowledge base** where autonomous agents synthesize, cross-link, index, and audit notes into immutable markdown. 

### 🚀 Key Advantages Over Other LLM Wiki Implementations
1. **Zero External Dependencies**: Pure Python standard library (`sqlite3`, `urllib.request`, `json`, `argparse`). No pip breakage, no LangChain bloat.
2. **0.007s SQLite FTS5 BM25 Ranked Search**: Sub-millisecond full-text retrieval across titles, tags, summaries, and content bodies.
3. **3-Tier LOD (Level of Detail)**: Eliminates 80% of LLM token waste by allowing agents to selectively recall LOD 1 (TL;DR Executive Summary) before fetching deep dives.
4. **Hierarchical MOC (Map of Contents)**: Prevents index context explosion via 2-tier MOCs (`index.md` + category sub-MOCs).
5. **Knowledge Compaction Diagnostics**: Automatically audits graph link density and alerts when fragmented micro-notes should be consolidated.
6. **Native Stdio MCP Server**: Ready out-of-the-box for Claude Desktop, Cursor, and Hermes Agent.

---

## 🏛️ Architecture & Data Flow

```
[Raw Sources / Session Logs]
             │
             ▼ (ingest)
   [sources/ Immutable Raw]
             │
             ▼ (synthesis)
     [wiki/ Markdown Vault] ── LOD 0 (YAML Frontmatter)
             │              ── LOD 1 (TL;DR Summary ~100 tokens)
             │              ── LOD 2 (Full Implementation Body)
             ▼
   ┌────────────────────────────────────────────────────────┐
   │                  Autonomous Engine                     │
   │  • SQLite FTS5 BM25 Engine (.wiki_cache/fts_index.db)  │
   │  • Hierarchical MOC Generator (Root + Category MOCs)   │
   │  • Integrity Linter & Knowledge Compaction Auditor     │
   │  • Native JSON-RPC stdio MCP Server                    │
   └────────────────────────────────────────────────────────┘
             ▲                                ▲
             │ (query --lod 1)                │ (tools/call)
   [Hermes / CLI Agents]             [Claude Desktop / Cursor]
```

---

## ⚡ Quick Start

### 1. Requirements
- Python 3.9 or higher (Vanilla macOS/Linux system python works out of the box).

### 2. Search & Recall (CLI)
```bash
# LOD 1 Search: 80% Token Savings (TL;DR Summary only)
python3 tools/wiki_manager.py query "Ghidra" --lod 1

# LOD 0 Search: Fast Metadata listing (~10 tokens)
python3 tools/wiki_manager.py query "Switch" --lod 0

# LOD 2 Search: Full markdown body
python3 tools/wiki_manager.py query "RomFS" --lod 2
```

### 3. Synchronize & Self-Heal Index
```bash
python3 tools/wiki_manager.py reindex
```

### 4. Graph Audit & Knowledge Compaction
```bash
python3 tools/wiki_manager.py audit
```

### 5. Ingest New Knowledge (7-Step Autonomous Pipeline)
```bash
python3 tools/wiki_manager.py ingest \
  --title "UE4 NIFM Service Stub" \
  --category "troubleshooting" \
  --content "## 요약 (TL;DR)\nNIFM stub is required for Unreal Engine 4 on Switch.\n\n## 상세\n..." \
  --tags "ue4,nintendo-switch,nifm"
```

---

## 🔌 Model Context Protocol (MCP) Setup

Connect your wiki directly to **Claude Desktop**, **Cursor**, or **Hermes Agent** as an external memory tool.

Add this entry to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "llm-wiki": {
      "command": "python3",
      "args": [
        "/ABSOLUTE/PATH/TO/Wiki/tools/mcp_server.py"
      ]
    }
  }
}
```

### Exposed MCP Tools
- `wiki_query`: Search via SQLite FTS5 BM25 with LOD (0, 1, 2) selection.
- `wiki_reindex`: Synchronize FTS5 index and generate MOCs.
- `wiki_audit`: Run graph connectivity and compaction diagnostics.
- `wiki_lint`: Validate schema and link integrity.

---

## 🧪 Testing

Run the zero-dependency test suite:
```bash
python3 -m unittest discover tools/tests
```

---

## 📄 License
This project is licensed under the [MIT License](LICENSE).
