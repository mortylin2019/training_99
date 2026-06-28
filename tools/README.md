# Reverse Engineering Tools

Tools for analyzing `99.exe` and extracting its data.

## Core Tools

### `extract_strings.py`
**Extract ALL strings and ranking data from the hex dump.**

- **Input**: `reverse_engineering_ref/decompiled/004063e4_hex` (memory dump of string pool at `0x004063e4`)
- **Output**:
  - `doc/game_strings.txt` — all 90+ extracted strings with indices
  - `doc/game_ranking.json` — 52 ranking entries as JSON
  - `doc/game_ranking_dump.txt` — human-readable ranking table
- **Features**:
  - Splits Shift-JIS string pool by 0xFF separators
  - XOR-decrypts ranking table (key 0xFF)
  - Maps ranking entry string IDs to decoded text

### `reverse_data.py`
~~Legacy ranking extractor~~ — removed. Use `extract_strings.py` instead.

### `dump_table.py`
**Live memory reader** — attaches to running `99.exe` process and dumps the velocity lookup tables (`0x00405d74`, `0x00406074`).

### `breakdown_and_translate.py`
**C code refactoring utility** — splits the decompiled `99.exe.c` into logical modules with Shift-JIS annotations and symbol renaming.

### `convert_icon.py`
**Icon converter** — extracts `.ico` from resources and converts to `.png`.

## Usage

```bash
# Extract all strings and ranking data
python tools/extract_strings.py

# Dump velocity tables from running game
python tools/dump_table.py

# Refactor and annotate decompiled C code
python tools/breakdown_and_translate.py
```
