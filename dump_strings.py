import sys

def solve():
    try:
        with open(r'c:\git\training_99\reverse_engineering_ref\decompiled\004063e4_hex', 'r') as f:
            full_hex = f.read().replace('\n', '').strip()
    except:
        print("File not found")
        return

    # User found that "便所掃除" matches in RAW mode (no XOR).
    # And we noticed 'FF' separators in the hex dump which seemed to align with the structure.
    # So we split by FF and decode as Shift-JIS.

    parts = full_hex.split('FF')
    
    found_strings = []
    
    print("--- Extracted Strings (Shift-JIS) ---")
    for i, p in enumerate(parts):
        if len(p) < 2: continue
        # Handle odd length if any
        if len(p) % 2 != 0: p = p[:-1]
        
        try:
            b = bytes.fromhex(p)
            text = b.decode("shift_jis")
            # Filter out likely garbage (control chars or too short)
            if len(text) > 1 and all(ord(c) >= 0x20 or ord(c) > 0x80 for c in text):
                found_strings.append(f"[{i}] {text}")
                print(f"[{i}] {text}")
        except:
            pass # Ignore decode errors

    with open(r'c:\git\training_99\doc\game_strings.txt', 'w', encoding='utf-8') as f:
        f.write("\n".join(found_strings))
    print(f"Saved {len(found_strings)} strings to doc/game_strings.txt")

if __name__ == "__main__":
    solve()
