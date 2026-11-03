# Source: Kirikae Switch AOT Recompilation Notes & Benchmarks

Date: 2026-11-03
Platform: macOS 27.2 Apple Silicon (M2)
Target: Nintendo Switch NSO (ARM64) -> Native Mach-O (ARM64)
Toolchain: Kirikae AOT recompiler, romfs-builder, nx2elf

## 1. RomFS Large Asset Bottlenecks
- Symptom: Dynamic directory binding on 10GB+ RomFS causes massive file descriptor exhaustion and high latency during UE4 asset streaming.
- Benchmark: Loading screen stalls for 45+ seconds with folder binding.
- Solution: Pack into flat `romfs.bin` via `romfs::build`. Map using IStorage (cmd 0/4) and inject via `KIRIKAE_ROMFS=romfs.bin`. Loading dropped to 3.2 seconds.

## 2. Kernel/OS Services Stubs
- fsp-srv cmd 200: `OpenDataStorageByCurrentProcess` required for UE4 file provider initialization.
- nifm:u: `CreateGeneralService` and `IRequest` stubs required to avoid infinite polling loop in network subsystem.

## 3. Coverage Profiling & Recompilation
- Profile collection: `kirikae run --record-profile execution.profile`
- 2nd stage build: `kirikae build --profile execution.profile`
- Hotspot: Zlib inflate loop promoted from interpreter loop to direct ARM64 instructions.
