# LLM Wiki Next-Gen Architecture Spec: SQLite FTS5, LOD, and Knowledge Compaction

- **Date**: 2026-11-03
- **Author**: Hermes Agent
- **Target**: `LLM Wiki Repository Root`
- **Status**: Approved for Planning

---

## 1. 개요 및 목적 (Executive Summary)

현재 LLM Wiki는 3계층(sources, wiki, index)과 기초 린터를 갖추었으나, 다음 세 가지 구조적 병목이 존재합니다:
1. **검색 한계**: 단순 부분 문자열 매칭(`if kw in text`)으로 동의어, 한/영 혼용, 형태소 검색 불가능.
2. **컨텍스트 낭비**: 에이전트가 문서를 조회할 때 전체 긴 마크다운을 통째로 읽어야 하여 토큰 소비 과다.
3. **인덱스 비대화**: 문서 수가 증가할수록 단일 평면 `index.md`가 비대해져 컨텍스트 윈도우를 압박.

본 설계는 **외부 의존성 제로(Zero-Dependency)** 원칙 하에 Python 내장 `sqlite3` FTS5 모듈을 활용하여 초고속 BM25 전문 검색을 구축하고, 3단계 상세도(LOD) 스키마와 계층형 MOC(Map of Contents), 지식 압축(Compaction) 진단 엔진을 도입합니다.

---

## 2. 핵심 아키텍처 구성요소

### 2.1 SQLite FTS5 기반 BM25 전문 검색 엔진
- **엔진**: Python 표준 라이브러리 `sqlite3` 내장 FTS5 (Full-Text Search 5) 가상 테이블.
- **캐시 위치**: `.wiki_cache/fts_index.db` (Git 추적 제외).
- **테이블 스키마**:
  ```sql
  CREATE VIRTUAL TABLE IF NOT EXISTS wiki_fts USING fts5(
      stem UNINDEXED,
      title,
      tags,
      summary,
      body,
      tokenize = 'unicode61'
  );
  ```
- **랭킹 가중치**:
  - `bm25(wiki_fts, 10.0, 5.0, 3.0, 1.0)`
  - Title(10.0) > Tags(5.0) > Summary(3.0) > Body(1.0)
- **증분 색인(Incremental Indexing)**:
  - 메타데이터 테이블(`wiki_meta`)에 파일별 `mtime`과 `sha256`을 저장하여, 변경된 파일만 선택적으로 FTS5 테이블에 upsert (색인 시간 10ms 이하).

### 2.2 3단계 상세도(Level of Detail, LOD) 스키마
에이전트의 토큰 소모를 최소화하고 인간의 옵시디언 가독성을 동시 충족하는 계층형 구조:

1. **LOD 0 (Frontmatter Metadata, ~10 tokens)**
   - YAML 메타데이터: `title`, `type`, `tags`, `sources`, `updated`, `related`.
2. **LOD 1 (Executive Summary / Resolution Matrix, ~50-100 tokens)**
   - 헤더: `## 요약 (TL;DR)` 또는 `## 개요`
   - 에이전트가 1차 검색 시 스캔하는 영역. 결론, 핵심 해결책 3줄, 제약 사항만 간결하게 포함.
3. **LOD 2 (Deep Dive & Implementation, ~500-2,000 tokens)**
   - 상세 배경, 전체 코드 블록, 디버깅 로그, 레퍼런스 표.

CLI 쿼리 지원:
```bash
python3 tools/wiki_manager.py query "Ghidra" --lod 1  # LOD 1 요약만 출력 (토큰 80% 절감)
python3 tools/wiki_manager.py query "Ghidra" --lod 2  # 전문 출력
```

### 2.3 계층형 MOC(Map of Contents) 인덱싱
- **루트 `index.md`**: 대분류별 핵심 주제 클러스터(MOC) 링크 및 최근 갱신 문서만 300토큰 이내로 유지.
- **서브 MOC**:
  - `wiki/concepts/index.md`
  - `wiki/tools/index.md`
  - `wiki/troubleshooting/index.md`
  - 각 카테고리 내부의 세부 문서 네트워크와 인바운드/아웃바운드 링크 관계를 집중 정리.

### 2.4 지식 압축 진단기 (Knowledge Compaction Engine)
- `tools/wiki_manager.py audit` 실행 시:
  - 동일한 태그나 공통 링크를 공유하는 마이크로 노트가 4개 이상 발견되면 **[Compaction Alert]** 발령.
  - 파편화된 노트들을 하나의 통합 가이드(Authoritative Guide)로 승격하고 기존 노트를 아카이브하도록 권고.

---

## 3. 인터페이스 및 CLI 계약 (CLI Interface Contract)

| 서브커맨드 / 플래그 | 인자 | 설명 |
| --- | --- | --- |
| `query` | `<검색어> [--lod 0\|1\|2] [--limit N]` | FTS5 BM25 랭킹 검색 및 LOD 지정 출력 |
| `reindex` | `[--force]` | FTS5 DB 증분 갱신 및 루트/서브 MOC index.md 자동 치유 |
| `audit` | - | 지식 그래프 연결도 + 압축 대상(Compaction) 클러스터 진단 |
| `lint` | - | Frontmatter 유효성, LOD 1 존재 여부, 링크 무결성 검증 |
| `ingest` | `--title --category --content [--source] [--tags]` | 7단계 자동 수집 및 FTS5 즉시 색인 |

---

## 4. 데이터 흐름도 (Data Flow)

```
[외부 소스 / 세션 로그]
       │
       ▼ (ingest)
[sources/ 불변 원본] ──► [wiki/ 마크다운 (LOD 0/1/2 규격)]
                                │
       ┌────────────────────────┴────────────────────────┐
       ▼                                                 ▼
[sqlite3 FTS5 인덱서 (.wiki_cache/)]            [계층형 MOC 갱신기]
       │                                                 │
       ▼ (query --lod 1)                                 ▼
[Hermes 에이전트 초고속 회상 (토큰 80% 절약)]         [Obsidian Vault MOC 탐색]
```

---

## 5. 비기능적 요구사항 (Non-Functional Requirements)

1. **Zero External Dependencies**: Python 3.9+ 표준 라이브러리(`sqlite3`, `urllib.request`, `json`, `re`, `os`, `sys`)만 사용.
2. **Speed**: 1,000개 문서 기준 쿼리 응답 시간 < 5ms.
3. **Safety**: 기존 6개 시드 문서의 데이터 유실 없이 무손실 마이그레이션.
