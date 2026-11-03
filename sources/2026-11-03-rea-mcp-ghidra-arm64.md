# Source: REA MCP Ghidra Setup & Architecture Notes

Date: 2026-11-03
Environment: macOS ARM64 (Apple Silicon), OpenJDK 21, Ghidra 12.1.3
Package: rea-agents@6.5.0

## Diagnostics & Requirements
1. Ghidra Version:
   - Ghidra 11.x - 12.1.x supported.
   - On macOS ARM64, Ghidra 12.1.3 includes native ARM64 decompiler binaries.
   - Requires wrapper `rea-mcp-wrapper.sh` to explicitly set `GHIDRA_INSTALL_DIR` and `JAVA_HOME`.
2. Binary Formats:
   - REA MCP natively recognizes ELF, Mach-O, PE.
   - NSO (Switch format) fails to parse by default.
   - Workaround A: Convert NSO to ELF64 using `nx2elf`.
   - Workaround B: Build Ghidra-Switch-Loader extension (`gradle -PGHIDRA_INSTALL_DIR=...`).
