# LLM Wiki Schema & Guidelines v2

이 위키는 안드레이 카파시(Andrej Karpathy)의 LLM Wiki 원칙에 따라 구축된 컴파일 타임 지식 엔진입니다.
사람이 읽기 좋고(Human-readable), AI가 자율적으로 유지보수(AI-maintained)하며, 런타임 RAG 검색 노이즈를 줄이고 작성 시점에 지식을 종합·정제합니다.

## 1. 디렉터리 계층 구조
- sources/: 웹 스크랩, 대화 원문, 빌드 로그, 에러 전문 등 불변(Immutable) 원본 데이터. AI가 임의로 수정하지 않으며 모든 위키 문서의 근거로 사용됨.
- wiki/: AI가 원본과 세션 데이터를 종합하여 컴파일한 핵심 지식 문서.
  - wiki/concepts/: 방법론, 아키텍처, 핵심 메커니즘
  - wiki/tools/: 도구, 라이브러리, CLI 환경 및 런타임 특성
  - wiki/troubleshooting/: 특정 에러 및 실전 해결 프로토콜
- index.md: 전체 위키 문서의 주제별 카탈로그 및 색인.
- log.md: 위키의 모든 추가 및 수정 내역이 누적되는 변경 일지.
- tools/: 위키 관리 및 서빙 도구 (`wiki_manager.py`, `server.sh`).

## 2. 문서 작성 규격 (Frontmatter Standard)
모든 `wiki/**/*.md` 문서는 상단에 다음 YAML Frontmatter를 필수로 포함해야 합니다:

```yaml
---
title: "문서 제목"
type: "concept" | "tool" | "troubleshooting"
tags: ["tag1", "tag2"]
sources:
  - "sources/YYYY-MM-DD-원본파일명.md"
updated: "YYYY-MM-DD"
related:
  - "[[관련문서]]"
---
```

### 필수 필드
- title: 문서의 공식 표제어.
- type: 문서의 범주 (`concept`, `tool`, `troubleshooting` 중 하나).
- tags: 검색 및 분류를 위한 키워드 배열.
- sources: 해당 지식의 근거가 되는 `sources/` 내 원본 파일 경로 목록.
- updated: 최종 수정 일자 (YYYY-MM-DD).

## 3. 상호 링크 규칙
- 문서 간 연결은 Obsidian/마크다운 표준 위키링크 `[[문서명]]` 형식을 사용합니다.
- 모든 위키 문서는 최소 1개 이상의 상호 링크 또는 관련 문서(`related`)를 지향합니다.
- 위키 본문 내에 가상의 placeholder 링크를 남기지 않으며, 실재하는 페이지만 링크합니다.

## 4. 정합성 검증 (Linter)
위키의 무결성을 검증하기 위해 다음 CLI 명령을 실행합니다:

```bash
python3 tools/wiki_manager.py lint
```

검증 항목:
1. YAML Frontmatter 필수 필드 존재 및 유효성
2. sources 참조 파일의 실재 여부 및 빈 파일 검출
3. `[[링크]]` 대상 문서의 실재 여부 (깨진 링크 검출)
4. index.md 내 문서 등재 여부 (고립 문서 방지)

## 5. 자율 진화 및 CLI 도구 (Autonomous Engine)
위키의 자가 발전과 무결성 유지를 위해 `tools/wiki_manager.py`에 다음 자율 도구가 탑재되어 있습니다:

### 자동 색인 및 사이드바 자가 치유 (Reindex)
모든 위키 문서의 Frontmatter와 요약을 자동 추출하여 `index.md`와 Docsify용 `_sidebar.md`를 갱신합니다:
```bash
python3 tools/wiki_manager.py reindex
```

### 지식 그래프 연결도 및 고립 문서 진단 (Audit)
문서 간 상호 인바운드/아웃바운드 링크 수를 전수 조사하여 연결도가 낮은 고립 후보 문서를 검출합니다:
```bash
python3 tools/wiki_manager.py audit
```

### 지식 베이스 검색 및 회상 (Query)
키워드를 기반으로 관련도 점수(제목, 태그, 본문 가중치)를 산출하여 핵심 요약과 출처를 조회합니다:
```bash
python3 tools/wiki_manager.py query "<검색어>"
```

### 자율 지식 수집 및 파이프라인 (Ingest)
외부 원본 데이터와 정리된 마크다운을 입력하면, 원본 아카이빙(sources/) → 위키 생성 → 자동 색인 → 로그 기록 → 린트 검증 → Git 커밋 → Discord 알림의 7단계를 1회 호출로 일괄 처리합니다:
```bash
python3 tools/wiki_manager.py --action ingest \
  --title "새 지식 제목" \
  --category concepts \
  --source "원본 로그/텍스트 또는 파일경로" \
  --content "## 개요\n내용..." \
  --tags "tag1,tag2" \
  --related "switch-aot-recompilation"
```
