#!/usr/bin/env python3
import sys
import json
import os
import io

# Ensure tools directory is in sys.path
TOOLS_DIR = os.path.abspath(os.path.dirname(__file__))
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

from fts_engine import FTSIndex
import wiki_manager

PROTOCOL_VERSION = "2024-11-05"

def send_response(response: dict):
    body = json.dumps(response, ensure_ascii=False)
    sys.stdout.write(body + "\n")
    sys.stdout.flush()

def handle_initialize(req_id, params):
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "llm-wiki-mcp",
                "version": "1.0.0"
            }
        }
    }

def handle_tools_list(req_id):
    tools = [
        {
            "name": "wiki_query",
            "description": "Search the LLM Wiki using SQLite FTS5 BM25 ranked full-text search. Supports 3-tier Level of Detail (LOD) to optimize LLM token usage.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query keywords (e.g. 'Ghidra', 'Switch RomFS', 'daemon launchd')"
                    },
                    "lod": {
                        "type": "integer",
                        "enum": [0, 1, 2],
                        "description": "Level of Detail: 0 (Metadata only, ~10 tokens), 1 (TL;DR Executive Summary, ~100 tokens, 80% token savings), 2 (Full Markdown Document)",
                        "default": 1
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        },
        {
            "name": "wiki_reindex",
            "description": "Synchronize FTS5 search index, regenerate root index.md (Map of Contents) and category sub-MOCs.",
            "inputSchema": {
                "type": "object",
                "properties": {}
            }
        },
        {
            "name": "wiki_audit",
            "description": "Audit wiki knowledge graph connectivity, analyze inbound/outbound links, and detect knowledge compaction candidates.",
            "inputSchema": {
                "type": "object",
                "properties": {}
            }
        },
        {
            "name": "wiki_lint",
            "description": "Validate YAML frontmatter schemas, sources presence, and [[wikilink]] integrity across the entire wiki.",
            "inputSchema": {
                "type": "object",
                "properties": {}
            }
        }
    ]
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "tools": tools
        }
    }

def handle_tools_call(req_id, params):
    name = params.get("name")
    args = params.get("arguments", {})

    # Capture stdout during tool execution
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()

    try:
        if name == "wiki_query":
            q = args.get("query", "")
            lod = args.get("lod", 1)
            limit = args.get("limit", 5)
            wiki_manager.query_wiki(q, lod=lod, limit=limit)
        elif name == "wiki_reindex":
            wiki_manager.reindex_wiki()
        elif name == "wiki_audit":
            wiki_manager.audit_wiki()
        elif name == "wiki_lint":
            wiki_manager.run_linter()
        else:
            sys.stdout = old_stdout
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32601,
                    "message": f"Method/Tool '{name}' not found."
                }
            }
    except Exception as e:
        sys.stdout = old_stdout
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [
                    {"type": "text", "text": f"Error executing {name}: {str(e)}"}
                ],
                "isError": True
            }
        }
    finally:
        sys.stdout = old_stdout

    output_text = buffer.getvalue().strip()
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "content": [
                {"type": "text", "text": output_text}
            ],
            "isError": False
        }
    }

def main():
    # Read line-delimited JSON-RPC from sys.stdin
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception:
            continue

        method = req.get("method")
        req_id = req.get("id")

        if method == "initialize":
            send_response(handle_initialize(req_id, req.get("params", {})))
        elif method == "notifications/initialized":
            pass # No response needed for notification
        elif method == "tools/list":
            send_response(handle_tools_list(req_id))
        elif method == "tools/call":
            send_response(handle_tools_call(req_id, req.get("params", {})))
        elif method == "ping":
            send_response({"jsonrpc": "2.0", "id": req_id, "result": {}})
        else:
            if req_id is not None:
                send_response({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32601,
                        "message": f"Unsupported method: {method}"
                    }
                })

if __name__ == "__main__":
    main()
