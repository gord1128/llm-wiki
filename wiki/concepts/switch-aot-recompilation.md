---
title: "Switch AOT 재컴파일 (Kirikae)"
type: "concept"
tags: ["nintendo-switch", "recompilation", "kirikae", "arm64", "apple-silicon"]
sources:
  - "sources/2026-11-03-kirikae-switch-aot.md"
updated: "2026-11-03"
related:
  - "[[ue4-romfs-nifm-bottleneck]]"
  - "[[rea-mcp-ghidra]]"
---

# Switch AOT 재컴파일 (Kirikae)

## 개요
닌텐도 스위치 ARM64 바이너리(NSO)를 Apple Silicon(ARM64) 네이티브 바이너리로 재컴파일(AOT, Ahead-Of-Time)하는 아키텍처 및 파이프라인.

관련 문서: [[ue4-romfs-nifm-bottleneck]], [[rea-mcp-ghidra]]

## 핵심 메커니즘
1. RomFS 바인딩 최적화
   - 10GB 이상의 대용량 RomFS 에셋은 개별 디렉터리 동적 바인딩 시 I/O 병목이 발생함.
   - `romfs::build` 도구로 단일 바이너리(`romfs.bin`)를 생성한 뒤, `KIRIKAE_ROMFS` 환경변수로 주입하고 IStorage(cmd 0/4) 매핑을 사용하는 것이 안정적임.

2. 언리얼 엔진 4 초기화 필수 조건
   - `fsp-srv cmd 200` (`OpenDataStorageByCurrentProcess`): RomFS 파일시스템 마운트용 스텁 필요.
   - `nifm:u` (`CreateGeneralService`, `IRequest`): 네트워크 초기화 단계 무한 대기 방지용 스텁 필요.

3. 2차 AOT 최적화 (핫스팟 인터프리터 오버헤드 제거)
   - 1차 실행 중 `.profile` 커버리지를 수집.
   - `kirikae build --profile <file>` 옵션으로 2차 AOT 빌드를 수행하여 Zlib 압축 해제 루프 등 핫스팟을 네이티브 코드로 승격.
