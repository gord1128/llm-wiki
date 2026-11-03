---
title: "LLM Wiki Architecture"
type: "concept"
tags: ["ai", "pkm", "llm-wiki", "karpathy", "architecture"]
sources:
  - "sources/2026-11-03-karpathy-llm-wiki-gist.md"
updated: "2026-11-03"
related:
  - "[[switch-aot-recompilation]]"
---

# LLM Wiki Architecture

## 개요
안드레이 카파시(Andrej Karpathy)가 제안한 개인 AI 지식 베이스 아키텍처. 질의 시점의 런타임 RAG 검색 노이즈를 극복하고, 지식 획득 시점(컴파일 타임)에 에이전트가 정보를 정제하여 마크다운 형태로 축적하는 시스템.

관련 문서: [[switch-aot-recompilation]], [[aside-discord-bot]]

## 3계층 아키텍처
1. sources/ (불변 원본 계층)
   - 스크랩한 웹 문서, 대화 로그, 에러 로그 원본을 그대로 보관.
   - AI가 원본을 임의로 수정하지 않으며 감사(Audit) 및 재가공의 근거로 사용.

2. wiki/ (AI 정제 지식 계층)
   - 개념(concepts), 도구(tools), 문제해결(troubleshooting)로 분류.
   - 상단 YAML Frontmatter, 3줄 요약, 상호 위키링크([[switch-aot-recompilation]]) 구조.

3. index.md & log.md (색인 및 일지 계층)
   - 모든 문서는 index.md에서 한 줄 설명과 함께 카탈로그화.
   - 추가 및 변경 내역은 log.md에 최신순으로 기록.

## 핵심 3대 운영 프로세스
- Ingest: 불변 원본을 읽고 위키 페이지 생성/합성 및 로그 기록.
- Query: 위키 색인과 링크를 탐색하여 최소 토큰으로 정밀 답변 도출.
- Lint: 깨진 링크, 미색인 문서, 메타데이터 누락을 스캔하여 지식 정합성 보장.
