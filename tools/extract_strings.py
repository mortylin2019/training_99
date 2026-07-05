"""
extract_strings.py — Extract ALL game strings and ranking data from the hex dump.

Reads `reverse_engineering_ref/decompiled/004063e4_hex` (the memory dump of the 
game's string pool and ranking table at address 0x004063e4).

Outputs:
  doc/game_strings.txt        — all strings in order with indices
  doc/game_ranking.json       — ranking table as JSON
  doc/game_ranking_dump.txt   — human-readable ranking table
"""

import struct
import json
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEX_FILE = os.path.join(BASE, "reverse_engineering_ref", "decompiled", "004063e4_hex")

def clean_string(s):
    """Strip display codes and control bytes, keep readable text only."""
    # Known English words that appear legitimately in strings
    known_en = {'MANIAC', 'COOL!', 'COOL', 'cute', 'paranoia'}
    
    # Strip leading non-CJK garbage (display codes like "lY}Ov}}Q}}]}=}7")
    # Check if string has CJK content
    has_cjk = any('\u3000' <= c <= '\u9FFF' or '\uFF00' <= c <= '\uFFEF' for c in s)
    if has_cjk:
        # Find the first CJK character
        for i, c in enumerate(s):
            if '\u3000' <= c <= '\u9FFF' or '\uFF00' <= c <= '\uFFEF':
                # But keep any preceding known English word
                prefix = s[:i].strip()
                if prefix and prefix.split()[-1].rstrip('!') not in known_en:
                    s = s[i:]
                break
    
    # Remove any remaining control characters
    cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]+', '', s)
    return cleaned.strip()

def main():
    # ── Read hex dump ─────────────────────────────────────────────
    with open(HEX_FILE, 'r') as f:
        raw_hex = f.read().replace('\n', '').replace('\r', '').strip()
    
    raw_bytes = bytes.fromhex(raw_hex)
    print(f"Hex dump: {len(raw_bytes)} bytes at 0x004063e4")

    # ── Extract string pool ───────────────────────────────────────
    # Strings are null-terminated. In this dump, 0xFF serves as the 
    # null/separator between strings (the code uses XOR decryption at runtime).
    # We split on 0xFF to get individual strings.
    
    POOL_END = 959  # byte offset where string pool ends, ranking table begins
    
    string_pool_raw = raw_bytes[:POOL_END]
    
    # Split by 0xFF separator
    parts = []
    current = bytearray()
    for b in string_pool_raw:
        if b == 0xFF:
            if current:
                parts.append(bytes(current))
                current = bytearray()
        else:
            current.append(b)
    if current:
        parts.append(bytes(current))
    
    strings = []
    for i, data in enumerate(parts):
        try:
            s = data.decode('shift_jis', errors='replace')
            s = clean_string(s)
            strings.append(s)
        except:
            strings.append(f"<DECODE_ERR_{i}>")
    
    print(f"String pool: {len(strings)} strings extracted")
    
    # ── Save all strings ──────────────────────────────────────────
    strings_path = os.path.join(BASE, "doc", "game_strings.txt")
    with open(strings_path, 'w', encoding='utf-8') as f:
        f.write("# 99.exe — All Game Strings\n")
        f.write("# Extracted from 0x004063e4 string pool\n\n")
        for i, s in enumerate(strings):
            if s.strip():
                f.write(f"[{i:3d}] {s}\n")
    print(f"  → {strings_path}")
    
    # ── Extract ranking table ─────────────────────────────────────
    # Starts at byte 959, 8 bytes per entry.
    # The table data IS XOR-encrypted with 0xFF in the dump.
    
    table_raw = raw_bytes[POOL_END:]
    
    rankings = []
    pos = 0
    while pos + 8 <= len(table_raw):
        entry = table_raw[pos:pos+8]
        # XOR decrypt
        decrypted = bytes([b ^ 0xFF for b in entry])
        
        threshold = struct.unpack('<I', decrypted[0:4])[0]
        id_prefix1 = decrypted[4]
        id_prefix2 = decrypted[5]
        id_title   = decrypted[6]
        id_suffix  = decrypted[7]
        
        def get_str(idx):
            if idx < len(strings) and strings[idx].strip():
                return strings[idx]
            return ""
        
        rankings.append({
            "threshold_ms": threshold,
            "threshold_s": threshold / 1000.0,
            "prefix1": get_str(id_prefix1),
            "prefix2": get_str(id_prefix2),
            "title":   get_str(id_title),
            "suffix":  get_str(id_suffix),
        })
        
        pos += 8
    
    # Filter: only keep entries with reasonable thresholds
    valid = [r for r in rankings if 0 < r["threshold_ms"] < 3600000]
    valid.sort(key=lambda r: r["threshold_ms"], reverse=True)
    print(f"Ranking table: {len(valid)} valid entries")
    
    # ── Save JSON ─────────────────────────────────────────────────
    json_path = os.path.join(BASE, "doc", "game_ranking.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(valid, f, ensure_ascii=False, indent=2)
    print(f"  → {json_path}")
    
    # ── Save human-readable ───────────────────────────────────────
    txt_path = os.path.join(BASE, "doc", "game_ranking_dump.txt")
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write("=== 99.exe Ranking Table ===\n\n")
        for r in valid:
            f.write(f"{r['threshold_s']:>7.1f}s  |  ")
            if r['prefix1']:
                f.write(f"{r['prefix1']}")
            if r['prefix2']:
                f.write(f"{r['prefix2']}")
            f.write(f"  [{r['title']}]  ")
            if r['suffix']:
                f.write(f"{r['suffix']}")
            f.write("\n")
    print(f"  → {txt_path}")
    
    # ── Preview ───────────────────────────────────────────────────
    print("\n--- Top 10 Rankings ---")
    for r in valid[:10]:
        title = f"{r['prefix1']}{r['prefix2']} [{r['title']}] {r['suffix']}".strip()
        print(f"  {r['threshold_s']:>6.1f}s  {title}")
    
    print("\n--- Notable Strings ---")
    notable = ["便所掃除", "特訓", "Enter", "speed", "reset", "絶妙"]
    for keyword in notable:
        for i, s in enumerate(strings):
            if keyword in s:
                print(f"  [{i:3d}] {s}")
                break

if __name__ == "__main__":
    main()
