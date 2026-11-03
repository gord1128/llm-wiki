# Plan: Open-Source Packaging, Security Sanitization & MCP Server for LLM Wiki

- **Date**: 2026-11-03
- **Author**: Hermes Agent (via `ulw-plan` & `ulw-research`)
- **Target Repository**: `LLM Wiki Repository Root`
- **Status**: Gated (Awaiting User Acceptance)

---

## 1. Context & Motivation

우리의 LLM Wiki는 순정 Python 3.9+ 표준 라이브러리만을 사용하여 0.007초 SQLite FTS5 BM25 전문 검색, 3-Tier LOD(토큰 80% 절감), 계층형 MOC, 지식 압축 진단기를 성공적으로 구축했습니다.
그러나 오픈소스 공개 및 생태계 경쟁력 관점에서 다음 3가지 핵심 결함이 확인되었습니다:
1. **보안/개인정보 노출**: 개인 Discord Bot 토큰 경로 및 특정 채널 ID가 `wiki_manager.py`에 하드코딩됨.
2. **상호운용성(Interoperability) 부재**: Claude Desktop, Cursor, Codex 등 표준 AI 에이전트 도구에서 호출할 수 있는 표준 MCP(Model Context Protocol) 인터페이스 부재.
3. **패키징 및 문서화 부재**: 누구나 클론해서 바로 쓸 수 있는 `README.md`, `.env.example`, `LICENSE`, 테스트 스위트 부재.

---

## 2. Target State & Success Criteria

| Target-State Difference | Task | Verification Scenario |
| --- | --- | --- |
| 1. Discord 개인정보 하드코딩 제거 | Task 1: Environment & Secrets Sanitization | `tools/wiki_manager.py` 내 채널 ID 검색 시 0건, 환경변수 부재 시 안내 후 안전 스킵 확인 |
| 2. 표준 stdio MCP 서버 제공 | Task 2: Zero-Dependency Stdio MCP Server | `tools/mcp_server.py`에 JSON-RPC ping/tools/list 및 query 호출 시 정상 응답 |
| 3. 오픈소스 표준 패키징 및 문서화 | Task 3: Packaging, License & Showcase README | 영문/한글 `README.md`, `LICENSE`(MIT), `.env.example` 완비 및 클론 후 원클릭 작동 |
| 4. 회귀 방지 통합 테스트 스위트 | Task 4: Automated Test Suite & CI Readiness | `python3 -m unittest discover tools/tests` 실행 시 FTS5, LOD, Linter 전체 100% PASS |

---

## 3. Work Breakdown (Ralplan Execution Lanes)

### Lane 1: Security Boundaries & Environment Sanitization (Size: S)
- **TASK**: 개인 디스코드 채널 ID 및 로컬 홈 경로 하드코딩 제거.
- **SCOPE**: `tools/wiki_manager.py`, `.env.example`
- **CHANGES**:
  - `WIKI_DISCORD_WEBHOOK_URL` 환경변수를 1차로 확인하도록 추상화.
  - 디스코드 알림이 설정되지 않아도 에러 없이 "알림 비활성화" 상태로 로컬 커밋 및 작업이 정상 완결되도록 예외 처리.
  - `.env.example` 파일 신설.
- **VERIFY**:
  - `grep -r "DISCORD_CHANNEL_ID" .` 확인 시 하드코딩된 특정 ID가 없음 확인.
  - 환경변수 없이 `python3 tools/wiki_manager.py reindex` 실행 시 0 에러 정상 완료.

### Lane 2: Zero-Dependency Stdio MCP Server (`tools/mcp_server.py`) (Size: M)
- **TASK**: 외부 무거운 프레임워크 없이 Python `sys.stdin`/`sys.stdout` 기반 JSON-RPC 2.0 표준 MCP 서버 구현.
- **SCOPE**: `tools/mcp_server.py`
- **TOOLS EXPOSED OVER MCP**:
  1. `wiki_query`: 검색어 및 LOD(0, 1, 2) 지정 고속 검색.
  2. `wiki_reindex`: 인덱스 및 MOC 동기화.
  3. `wiki_audit`: 그래프 연결도 및 압축 진단 리포트.
  4. `wiki_lint`: 무결성 검증.
- **VERIFY**:
  - CLI 파이프로 JSON-RPC `tools/list` 요청 전달 시 JSON 스키마 정상 반환 확인.
  - Claude Desktop / Cursor 설정 JSON 템플릿 제공.

### Lane 3: Open-Source Repository Packaging (Size: S)
- **TASK**: 글로벌 오픈소스 저장소 표준 파일 작성.
- **SCOPE**: `README.md`, `LICENSE` (MIT), `CONTRIBUTING.md`, `.gitattributes`
- **CONTENT**:
  - Karpathy 아키텍처 다이어그램 (ASCII / Markdown).
  - 0.007s FTS5 벤치마크 및 80% 토큰 절감 LOD 소개.
  - Claude Desktop / Cursor 연동 가이드.
- **VERIFY**: Docsify 및 GitHub 렌더링 검증.

### Lane 4: Automated Test Suite (`tools/tests/`) (Size: S)
- **TASK**: 삭제되었던 테스트를 공식 테스트 스위트로 복원 및 확장.
- **SCOPE**: `tools/tests/test_fts.py`, `tools/tests/test_lod.py`
- **VERIFY**:
  - `python3 -m unittest discover tools/tests` 전수 통과 (Exit code 0).

---

## 4. Risks & Mitigations

1. **위키 데이터와 엔진 결합 리스크**:
   - 현재 리포지토리에 존재하는 6개 시드 문서는 훌륭한 "실제 쇼케이스 예시(Showcase Examples)"로 기능하므로 유지하되, 개인 토큰이나 기밀 경로가 포함되지 않도록 린터 검사를 거칩니다.
2. **MCP 서버 순정 호환성 리스크**:
   - `uv`나 `pip` 설치 없이 시스템 Python 3.9+ 어디서나 단독 실행(`python3 tools/mcp_server.py`)될 수 있도록 순수 JSON-RPC 파서로 구현하여 외부 의존성 제로를 유지합니다.
