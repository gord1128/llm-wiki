---
title: "UE4 Switch 포팅 RomFS 및 nifm 병목 해결"
type: "troubleshooting"
tags: ["ue4", "nintendo-switch", "kirikae", "romfs", "nifm", "optimization"]
sources:
  - "sources/2026-11-03-kirikae-switch-aot.md"
updated: "2026-11-03"
related:
  - "[[switch-aot-recompilation]]"
---

# UE4 Switch 포팅 RomFS 및 nifm 병목 해결

## 문제 현상
- Kirikae로 재컴파일한 언리얼 엔진 4 기반 Switch 게임 실행 시 무한 대기 또는 극심한 프레임 드랍 발생.

관련 문서: [[switch-aot-recompilation]]

## 해결 절차
1. RomFS 바인딩 변경
   - 폴더 트리 마운트 방식을 버리고 `romfs.bin` 단일 이미지로 빌드 후 환경변수 매핑.
2. 서비스 스텁 보강
   - `fsp-srv` 커맨드 200(OpenDataStorageByCurrentProcess) 응답 구현.
   - `nifm:u` 네트워크 통신 스텁 통과.
3. 2차 프로파일 기반 컴파일
   - 1차 실행 프로파일(`.profile`) 수집 후 `kirikae build --profile`로 zlib 압축 해제 핫스팟 제거.
