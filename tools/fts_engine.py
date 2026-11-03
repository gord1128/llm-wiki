#!/usr/bin/env python3
import os
import sqlite3
import re

DEFAULT_CACHE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".wiki_cache"))
DEFAULT_DB_PATH = os.path.join(DEFAULT_CACHE_DIR, "fts_index.db")

class FTSIndex:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self):
        cur = self.conn.cursor()
        # 1. 메타데이터 테이블 (증분 인덱싱 추적용)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS wiki_meta (
                stem TEXT PRIMARY KEY,
                mtime REAL,
                title TEXT
            )
        """)
        # 2. FTS5 가상 테이블
        cur.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS wiki_fts USING fts5(
                stem UNINDEXED,
                title,
                tags,
                summary,
                body,
                tokenize = 'unicode61'
            )
        """)
        self.conn.commit()

    def index_document(self, stem: str, title: str, tags: list, summary: str, body: str, mtime: float) -> bool:
        cur = self.conn.cursor()
        # 증분 검사: 기존 mtime과 동일하면 스킵
        cur.execute("SELECT mtime FROM wiki_meta WHERE stem = ?", (stem,))
        row = cur.fetchone()
        if row and row["mtime"] == mtime:
            return False

        # 기존 레코드 제거
        cur.execute("DELETE FROM wiki_meta WHERE stem = ?", (stem,))
        cur.execute("DELETE FROM wiki_fts WHERE stem = ?", (stem,))

        tags_str = " ".join(tags) if isinstance(tags, list) else str(tags)
        
        # 새 레코드 삽입
        cur.execute(
            "INSERT INTO wiki_fts (stem, title, tags, summary, body) VALUES (?, ?, ?, ?, ?)",
            (stem, title, tags_str, summary, body)
        )
        cur.execute(
            "INSERT INTO wiki_meta (stem, mtime, title) VALUES (?, ?, ?)",
            (stem, mtime, title)
        )
        self.conn.commit()
        return True

    def sync_all(self, docs: list, force: bool = False) -> int:
        cur = self.conn.cursor()
        if force:
            cur.execute("DELETE FROM wiki_meta")
            cur.execute("DELETE FROM wiki_fts")
            self.conn.commit()

        updated_count = 0
        current_stems = set()

        for d in docs:
            stem = d["stem"]
            current_stems.add(stem)
            mtime = 0.0
            if os.path.exists(d.get("path", "")):
                mtime = os.path.getmtime(d["path"])
                
            is_updated = self.index_document(
                stem=stem,
                title=d.get("title", stem),
                tags=d.get("tags", []),
                summary=d.get("summary", ""),
                body=d.get("body", ""),
                mtime=mtime
            )
            if is_updated:
                updated_count += 1

        # 삭제된 문서 정리
        cur.execute("SELECT stem FROM wiki_meta")
        for row in cur.fetchall():
            s = row["stem"]
            if s not in current_stems:
                cur.execute("DELETE FROM wiki_meta WHERE stem = ?", (s,))
                cur.execute("DELETE FROM wiki_fts WHERE stem = ?", (s,))
        self.conn.commit()
        return updated_count

    def search(self, query: str, limit: int = 5) -> list:
        if not query or not query.strip():
            return []

        # FTS5 쿼리 새니타이징: 특수문자 제거 및 토큰화
        raw_tokens = re.findall(r"[\w가-힣]+", query)
        if not raw_tokens:
            return []

        # 각 토큰에 대해 접두사(*) 와일드카드 매칭 조합
        fts_query = " OR ".join([f'"{tok}"*' for tok in raw_tokens])

        cur = self.conn.cursor()
        try:
            # FTS5 bm25() returns negative score (lower/more negative is better match)
            # Normalize to positive score with higher precision (6 decimal places)
            cur.execute("""
                SELECT 
                    stem, 
                    title, 
                    tags, 
                    summary, 
                    bm25(wiki_fts, 10.0, 5.0, 3.0, 1.0) AS score,
                    snippet(wiki_fts, 4, '<b>', '</b>', '...', 15) AS snippet_text
                FROM wiki_fts
                WHERE wiki_fts MATCH ?
                ORDER BY score ASC
                LIMIT ?
            """, (fts_query, limit))

            results = []
            for row in cur.fetchall():
                # FTS5 bm25 score can be very small numbers (e.g. -1.5e-06)
                # Scale by 1e6 for human-readable intuitive relevance score
                raw_bm25 = row["score"]
                relevance_score = round(abs(raw_bm25) * 1_000_000, 2)
                results.append({
                    "stem": row["stem"],
                    "title": row["title"],
                    "tags": [t for t in row["tags"].split() if t],
                    "summary": row["summary"],
                    "score": relevance_score,
                    "snippet": row["snippet_text"]
                })
            return results
        except sqlite3.OperationalError as e:
            # 쿼리 문법 에러 시 단순 LIKE 폴백
            fallback_q = f"%{query.strip()}%"
            cur.execute("""
                SELECT stem, title, tags, summary, 1.0 AS score, '' AS snippet_text
                FROM wiki_fts
                WHERE title LIKE ? OR tags LIKE ? OR summary LIKE ?
                LIMIT ?
            """, (fallback_q, fallback_q, fallback_q, limit))
            return [dict(r) for r in cur.fetchall()]

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
