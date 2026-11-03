---
title: "Aside 디스코드 봇 운용 구조"
type: "tool"
tags: ["discord", "aside", "bot", "macos", "daemon"]
sources:
  - "sources/2026-11-03-macos-launchd-exit-78.md"
updated: "2026-11-03"
related:
  - "[[launchd-external-volume-exit-78]]"
---

# Aside 디스코드 봇 아키텍처

## 개요
외장 SSD 볼륨에 위치한 브라우저 연동 및 자동화 디스코드 봇 운용 프로토콜.

관련 문서: [[launchd-external-volume-exit-78]], [[llm-wiki-architecture]]

## 운용 구조
1. launchd 대신 PID 기반 데몬 사용
   - macOS의 launchd(LaunchAgent)는 외장 볼륨 마운트 타이밍 권한 이슈로 `exit 78 (EX_CONFIG)` 에러가 발생함.
   - 해결책: 외장 드라이브 내 `service.sh` 셸 스크립트를 통해 백그라운드 PID 관리 방식으로 안정적 구동.

2. 다중 계정 접근 권한
   - 주 계정 및 부 계정(`1310873669089624114`, `@명건@`) 허용 등록 완료.
