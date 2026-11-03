#!/usr/bin/env python3
import unittest
import os
import sys

# Ensure tools directory is in sys.path
TOOLS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

from fts_engine import FTSIndex
import wiki_manager

class TestWikiFTSAndLOD(unittest.TestCase):
    def setUp(self):
        self.test_db = "/tmp/test_wiki_fts_suite.db"
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        self.fts = FTSIndex(db_path=self.test_db)

    def tearDown(self):
        self.fts.close()
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_fts5_indexing_and_bm25_ranking(self):
        # 문서 2건 인덱싱
        self.fts.index_document(
            stem="nintendo-kirikae",
            title="Nintendo Switch Kirikae Recompilation",
            tags=["switch", "kirikae", "arm64"],
            summary="AOT recompilation pipeline.",
            body="Kirikae translates Switch NSO binaries into native Apple Silicon ARM64 instructions.",
            mtime=1.0
        )
        self.fts.index_document(
            stem="ghidra-mcp",
            title="Ghidra Reverse Engineering Protocol",
            tags=["ghidra", "mcp"],
            summary="Decompiler MCP tools.",
            body="Ghidra 12 decompiler automation via MCP on macOS.",
            mtime=1.0
        )

        # 1. 'Switch' 검색 시 kirikae 문서 우선 매칭 확인
        res = self.fts.search("Switch")
        self.assertTrue(len(res) > 0)
        self.assertEqual(res[0]["stem"], "nintendo-kirikae")
        self.assertIn("score", res[0])

        # 2. 'Ghidra' 검색 확인
        res_g = self.fts.search("Ghidra")
        self.assertTrue(len(res_g) > 0)
        self.assertEqual(res_g[0]["stem"], "ghidra-mcp")

    def test_lod1_summary_extraction(self):
        body_with_tldr = """
## 요약 (TL;DR)
핵심 결론 첫 번째 줄.
핵심 해결책 두 번째 줄.

## 세부 내용
여기는 긴 본문 내용입니다.
"""
        lod1 = wiki_manager.extract_lod1(body_with_tldr)
        self.assertIn("핵심 결론", lod1)
        self.assertNotIn("여기는 긴 본문", lod1)

    def test_wiki_linter_zero_errors(self):
        exit_code = wiki_manager.run_linter()
        self.assertEqual(exit_code, 0)

if __name__ == "__main__":
    unittest.main()
