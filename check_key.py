import sys
sys.stdout.reconfigure(encoding='utf-8')

known_text = "便所掃除"
try:
    sjis_bytes = known_text.encode('shift_jis')
    print(f"Known Text: {known_text}")
    print(f"Shift-JIS Hex: {sjis_bytes.hex().upper()}")
    
    xored = bytes(x ^ 0xFF for x in sjis_bytes)
    print(f"XORed (0xFF) Hex: {xored.hex().upper()}")

    # Now let's try to decrypt the whole file with this assumption confirmed/refuted
    with open(r'c:\git\training_99\reverse_engineering_ref\decompiled\004063e4_hex', 'r') as f:
        full_hex = f.read().replace('\n', '').strip()

    print("\n--- Searching for this pattern in file ---")
    if xored.hex().upper() in full_hex.upper():
        print("FOUND MATCH! The encryption is definitely XOR 0xFF.")
    else:
        print("NO MATCH. Maybe offset or key is different?")
        
    # Let's try to decode specifically the last few lines which look like settings
    # The hex dump showed "7265736574" at the end which is "reset" in ASCII
    # "7370656564" is "speed"
    # These were visibly PLAIN ASCII in the hex dump at the end (lines 170+ in hex view).
    # But the User said "decrypt" yielded garbage for [176] etc.
    
    # Wait! In the previous output:
    # [176] !NLQ忽建
    # [185] 償込草満
    
    # "償込草満" looks Chinese/Kanji-ish. 
    # "便所掃除" (Toilet Cleaning) -> ShiftJIS: 95D6 8F8A 917C 8F9C
    # XOR FF -> 6A29 7075 6E83 7063
    
    parts = full_hex.split('FF')
    for i, p in enumerate(parts):
        if len(p) < 4: continue
        try:
            b = bytes.fromhex(p)
            # Try 1: XOR FF then Shift-JIS
            dec1 = bytes(x ^ 0xFF for x in b)
            s1 = dec1.decode("shift_jis", errors="ignore")
            
            # Try 2: NO XOR, just Shift-JIS (maybe some parts are plain?)
            s2 = b.decode("shift_jis", errors="ignore")

            if known_text in s1:
                 print(f"[{i}] MATCH XOR+SJIS: {s1}")
            if known_text in s2:
                 print(f"[{i}] MATCH RAW+SJIS: {s2}")
                 
        except:
            pass
            
except Exception as e:
    print(e)
