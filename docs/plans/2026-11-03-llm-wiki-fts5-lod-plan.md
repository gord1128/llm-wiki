# [LLM Wiki Next-Gen] FTS5 Search, 3-Tier LOD, & Compaction Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** SQLite FTS5 기반의 BM25 전문 검색 엔진, 3-Tier LOD(Level-of-Detail) 요약 체계, 계층형 MOC 및 지식 압축 진단기를 제로 의존성(Python stdlib)으로 구축하여 위키의 검색 속도와 에이전트 토큰 효율을 극대화한다.

**Architecture:** 
- 독립 모듈 `tools/fts_engine.py`가 `.wiki_cache/fts_index.db`에 FTS5 가상 테이블을 생성하고 증분 BM25 인덱싱 및 랭킹 쿼리를 담당한다.
- `tools/wiki_manager.py`가 FTS5 엔진을 임포트하여 `query`, `reindex`, `ingest`와 유기적으로 통합하며, `--lod 0|1|2` 인수를 통해 최소 토큰으로 요약본만 선택 추출한다.
- `reindex`와 `audit`은 계층형 MOC(카테고리별 index.md) 생성 및 태그 중복 마이크로 노트를 감지하여 지식 압축(Compaction) 알림을 발행한다.

**Tech Stack:** Python 3.9+ 표준 라이브러리 (`sqlite3` FTS5, `re`, `json`, `urllib.request`, `argparse`, `glob`, `os`, `sys`).

**Spec:** `docs/specs/2026-11-03-llm-wiki-fts5-lod-design.md`

## Global Constraints
- Python 외부 패키지(pip) 절대 사용 금지 (오직 Python stdlib 모듈만 사용).
- `.wiki_cache/` 디렉터리는 Git 추적에서 제외 (`.gitignore` 등록).
- 기존 6개 시드 문서의 데이터는 100% 무손실 보존되며 LOD 규격에 맞게 점진적 보강.
- macOS 시스템 파이썬(`/usr/bin/python3`) 및 최신 파이썬 모두에서 무경고 정상 구동 보장.

## Review Focus
1. SQLite FTS5 구문 토큰화: 영문 단어와 한글 어절이 혼합된 쿼리에서 구문 오류(Syntax Error) 없이 부분 매칭 및 랭킹이 정상 산출되는가?
2. 증분 인덱싱 안정성: 파일이 수정되지 않았을 때 불필요한 FTS 재색인을 건너뛰고, 파일이 삭제되거나 수정되면 즉시 반영되는가?
3. LOD 1 추출 신뢰성: 다양한 헤더 스타일(`## 요약`, `## 개요`, `## TL;DR`)에서도 LOD 1 요약본을 정확히 추출하는가?
4. 빈 쿼리 또는 매칭 불발 시: 예외(Exception)로 중단되지 않고 사용자 친화적인 메시지와 안내를 반환하는가?
5. MOC 디렉터리 생성: 서브 카테고리 디렉터리가 없을 때도 안전하게 생성 및 복구되는가?

---

### Task 1: Zero-Dependency SQLite FTS5 Engine (`tools/fts_engine.py`)

**Files:**
- Create: `tools/fts_engine.py`
- Test: `tools/test_fts.py`

**Interfaces:**
- Produces:
  * `class FTSIndex`:
    - `__init__(db_path: str = None)`
    - `index_document(stem: str, title: str, tags: list[str], summary: str, body: str, mtime: float) -> bool`
    - `sync_all(docs: list[dict], force: bool = False) -> int`
    - `search(query: str, limit: int = 5) -> list[dict]`
    - `close()`

- [ ] **Step 1: Write unit test `tools/test_fts.py`**
  - 가상 문서 3건 인덱싱 후, BM25 랭킹 검색 및 증분 인덱싱 확인 테스트 작성.
  
- [ ] **Step 2: Run test to verify it fails**
  - Run: `python3 tools/test_fts.py`
  - Expected: FAIL (`ModuleNotFoundError: No module named 'tools.fts_engine'`)

- [ ] **Step 3: Implement `tools/fts_engine.py`**
  - `sqlite3` FTS5 가상 테이블 및 메타데이터 추적 테이블 생성.
  - `bm25()` 랭킹 산출 로직 구현.
  
- [ ] **Step 4: Run test to verify it passes**
  - Run: `python3 tools/test_fts.py`
  - Expected: PASS

- [ ] **Step 5: Git commit**
  - `git add tools/fts_engine.py tools/test_fts.py .gitignore`
  - `git commit -m "feat(fts): add zero-dependency SQLite FTS5 BM25 search engine"`

---

### Task 2: 3-Tier LOD (Level of Detail) Parser & CLI Integration

**Files:**
- Modify: `tools/wiki_manager.py`
- Modify: `SCHEMA.md`

**Interfaces:**
- Consumes: `FTSIndex` from `tools/fts_engine.py`
- Produces:
  * `parse_doc_lods(content: str) -> dict`: `{lod0: fm, lod1: summary, lod2: body}`
  * `wiki_manager.py query <keyword> [--lod 0|1|2] [--limit N]`

- [ ] **Step 1: Write LOD parser & CLI integration tests**
  - 테스트 케이스: `--lod 1` 요청 시 본문(LOD 2)을 제외한 요약본만 정확히 반환하는지 검증.

- [ ] **Step 2: Implement LOD extractor in `tools/wiki_manager.py`**
  - 정규식을 통해 `## 요약 (TL;DR)`, `## 개요` 섹션을 LOD 1으로 규격화하여 추출.
  - `query` 커맨드가 `fts_engine.search()` 결과를 받아 지정된 LOD 레벨로 서식화하여 출력.

- [ ] **Step 3: Verify with real queries**
  - Run: `python3 tools/wiki_manager.py query "Ghidra" --lod 1`
  - Run: `python3 tools/wiki_manager.py query "RomFS" --lod 2`

- [ ] **Step 4: Git commit**
  - `git add tools/wiki_manager.py SCHEMA.md`
  - `git commit -m "feat(lod): integrate FTS5 engine and 3-tier LOD query support"`

---

### Task 3: Hierarchical MOC & Knowledge Compaction Engine

**Files:**
- Modify: `tools/wiki_manager.py`

**Interfaces:**
- Produces:
  * `generate_hierarchical_mocs() -> None`: 루트 `index.md` 간소화 및 `wiki/<category>/index.md` 서브 MOC 생성.
  * `detect_compaction_candidates(docs: list[dict]) -> list[dict]`: 3개 이상 유사 태그 집중 문서 탐지.

- [ ] **Step 1: Implement MOC generator in `reindex_wiki()`**
  - 루트 `index.md`는 대분류 MOC 링크와 최근 수정 문서 5건만 컴팩트하게 표시.
  - 각 카테고리 폴더(`wiki/concepts/`, `wiki/tools/`, `wiki/troubleshooting/`)에 개별 `index.md` 생성.

- [ ] **Step 2: Implement Compaction Detector in `audit_wiki()`**
  - 태그 및 공통 링크 클러스터 분석으로 통합 후보군 추천.

- [ ] **Step 3: Verify MOC generation and compaction alerts**
  - Run: `python3 tools/wiki_manager.py reindex`
  - Run: `python3 tools/wiki_manager.py audit`

- [ ] **Step 4: Git commit**
  - `git add tools/wiki_manager.py`
  - `git commit -m "feat(moc): implement hierarchical MOC and knowledge compaction alerts"`

---

### Task 4: End-to-End Verification & Seed Docs LOD Enrichment

**Files:**
- Modify: `wiki/**/*.md` (6개 시드 문서)
- Remove: `tools/test_fts.py` (임시 테스트 파일 정리)

- [ ] **Step 1: Enrich 6 seed docs with explicit `## 요약 (TL;DR)` section**
  - 모든 시드 문서에 3줄 핵심 결론을 담은 명시적 TL;DR 섹션 추가.

- [ ] **Step 2: Run complete linter & audit**
  - Run: `python3 tools/wiki_manager.py lint`
  - Run: `python3 tools/wiki_manager.py audit`

- [ ] **Step 3: Final Git commit and status report**
  - `git commit -m "docs: enrich seed wiki documents with standardized LOD-1 TL;DR"`
