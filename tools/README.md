# Reverse Engineering Tools

This directory contains the primary scripts used for analyzing `99.exe` and generating the project assets.

## Core Tools

### 1. `breakdown_and_translate.py`
**Purpose**: The main reverse engineering utility.
- **Input**: 
  - `reverse_engineering_ref/decompiled/99.exe.c` (Raw decompiled C)
  - `reverse_engineering_ref/decompiled/004063e4_hex` (String data dump)
  - `reverse_engineering_ref/decompiled/manual_strings.csv` (Manual overrides)
- **Output**: 
  - `reverse_engineering_ref/python_breakdown/*.c` (Refactored C files)
- **Features**:
  - Splits the monolithic C file into logical modules (e.g., `Stage1_StartScreen.c`).
  - Decodes Shift-JIS strings from the hex dump and inserts them as comments inline.
  - Applies manual string overrides for better readability.
  - Translates function and variable names based on a predefined symbol map.

### 2. `reverse_data.py`
**Purpose**: Data extraction for the Flask web application.
- **Input**:
  - `reverse_engineering_ref/decompiled/004063e4_hex`
- **Output**:
  - `flask_app/static/rankings.json` (Game ranking logic for the web UI)
  - `doc/game_ranking_dump.txt` (Human readable dump)
- **Features**:
  - Parses the game's internal ranking table (starting at offset 959).
  - Decrypts the XOR-obfuscated data.
  - Exports the data in JSON format for the web frontend.

## Usage

To regenerate the C code breakdown:
```bash
uv run tools/breakdown_and_translate.py
```

To update the web app data:
```bash
uv run tools/reverse_data.py
```
