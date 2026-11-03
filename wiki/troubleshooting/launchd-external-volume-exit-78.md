---
title: "macOS launchd 외장 볼륨 Exit 78 해결"
type: "troubleshooting"
tags: ["macos", "launchd", "external-volume", "exit-78", "daemon"]
sources:
  - "sources/2026-11-03-macos-launchd-exit-78.md"
updated: "2026-11-03"
related:
  - "[[aside-discord-bot]]"
---

# macOS launchd 외장 볼륨 Exit 78 해결

## 원인
- macOS의 LaunchAgent는 시스템 부팅 시점에 즉시 실행되는데, 외장 하드(`/Volumes/Hyeonssd`)가 아직 완전히 마운트되지 않았거나 TCC 디스크 접근 권한이 상속되지 않아 `EX_CONFIG (78)` 종료 코드가 발생함.

관련 문서: [[aside-discord-bot]]

## 해결책
- launchd에 직접 등록하지 않고, 자체 PID 관리 스크립트(`service.sh start/stop/status`)를 생성하여 실행하거나 로그인 후 마운트 완료 확인 후 실행하는 래퍼를 사용함.
