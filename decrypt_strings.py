import sys

def solve():
    try:
        with open(r'c:\git\training_99\reverse_engineering_ref\decompiled\004063e4_hex', 'r') as f:
            full_hex = f.read().replace('\n', '').strip()
    except FileNotFoundError:
        print("Hex file not found.")
        return

    # Split by 'FF' which we hypothesize is the terminator
    parts = full_hex.split('FF')
    
    print("--- Decrypted Strings (XOR 0xFF, Shift-JIS) ---")
    for i, p in enumerate(parts):
        if not p: continue
        try:
            # Handle potential odd length hex strings (nibble issues)
            if len(p) % 2 != 0:
                p = p[:-1] # Truncate last nibble if necessary
            
            b = bytes.fromhex(p)
            
            # XOR with 0xFF
            dec = bytes(x ^ 0xFF for x in b)
            
            # Decode
            text = dec.decode("shift_jis", errors="replace")
            print(f"[{i}] {text}")
        except Exception as e:
            print(f"[{i}] ERROR: {e}")

if __name__ == "__main__":
    solve()
