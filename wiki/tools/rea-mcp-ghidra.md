---
title: "REA MCP & Ghidra 12.x 역공학 환경"
type: "tool"
tags: ["ghidra", "rea-mcp", "reverse-engineering", "arm64", "apple-silicon"]
sources:
  - "sources/2026-11-03-rea-mcp-ghidra-arm64.md"
updated: "2026-11-03"
related:
  - "[[switch-aot-recompilation]]"
---

# REA MCP & Ghidra 12.x 역공학 환경

## 개요
macOS Apple Silicon 환경에서 바이너리 분석 및 Ghidra 툴체인을 MCP(Model Context Protocol)로 연동하는 프로토콜.

관련 문서: [[switch-aot-recompilation]]

## 구성 요소 및 주의사항
1. 호환성 및 Java 환경
   - Ghidra 11.x ~ 12.1.x 및 Java 21 이상 요구.
   - macOS ARM64 환경에서는 decompiler 바이너리가 포함된 12.1.3 빌드 사용 필요.
   - 환경변수: `GHIDRA_INSTALL_DIR`, `JAVA_HOME` 래퍼 스크립트 지정 필수.

2. NSO 파일 로드
   - REA MCP는 ELF, Mach-O, PE 형식만 기본 인식.
   - 닌텐도 스위치 NSO 바이너리는 `nx2elf`로 ELF64로 사전 변환하거나, Ghidra-Switch-Loader 확장을 빌드하여 설치해야 정상 디컴파일 가능.
