# Reverse Engineering Summary: 99.exe (Training 99)

## Overview
This document summarizes the findings from the reverse engineering analysis of the `99.exe` binary. 
The primary goal was to reconstruct the gameplay logic and extract the authentic ranking/title system.

## Data Structures

### 1. String Pool (`DAT_004063e4`)
- **Location:** Offset 0 in the hex dump provided (mapped to memory address `0x004063e4`).
- **Format:** A continuous block of Null-terminated Shift-JIS strings.
- **Encryption:** 
  - In the provided hex dump (`004063e4_hex`), these strings appear as **RAW / Plaintext**.
  - However, the decompiled code (`FUN_00402208`) suggests they are XOR encrypted at runtime. This indicates the hex dump likely captures the memory state *after* initialization or from a resource segment that tools automatically decoded.
- **Key Verification:** The string "便所掃除" (Toilet Cleaning) was found at index 73, confirming the encoding is Shift-JIS.
- **Content:** Contains ranking titles, suffixes (e.g., "と認定する。"), and debug commands ("speed", "reset").

### 2. Ranking Logic Table (`DAT_004067a3`)
- **Location:** Immediately following the string pool (Offset 959 / 0x3BF in dump).
- **Format:** An array of 8-byte structures.
- **Structure:**
  ```c
  struct RankEntry {
      uint32_t threshold_ms; // Survival time in milliseconds
      uint8_t unknown1;
      uint8_t unknown2;
      uint8_t title_id_main;   // Index into String Pool
      uint8_t title_id_suffix; // Index into String Pool
  };
  ```
- **Encryption:**
  - Unlike the strings, this table section **IS XOR Encrypted** in the dump with `0xFF`.
  - To read the values, every byte must be XOR'd with `0xFF`.
  - Confirmed by the fact that `threshold` becomes a valid integer sequence (180000, 175000...) only after inversion.

## Extracted Game Data

### Difficulty Levels
Reversed from `FUN_00404660`:
- **Level 1 (Easy):** 30 Bullets
- **Level 2 (Normal):** 50 Bullets (Default)
- **Level 3 (Hard):** 100 Bullets
- **Level 4 (Lunatic):** 200 Bullets

### Ranking System (Top 5)
1. **180s+**: 愛の人勢いのある (Person of Love, Full of Momentum)
2. **170s+**: 奇跡の人勢いのある (Miracle Person, Full of Momentum)
3. **100s+**: 達人以上。 (Master or higher)
4. **55s+**: ダンスマニア何やってんだ (Dance Maniac, What are you doing?)
5. **8.0s+**: 便所掃除と認定する。 (Certified as: Toilet Cleaner)

## Tools
A unified extraction tool is available at:
`c:\git\training_99\tools\reverse_data.py`

Usage:
```bash
python tools/reverse_data.py
```
This script reads the hex dump, validates the "Toilet Cleaning" key, and generates `rankings.json` for the web remake.
