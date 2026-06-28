import sys
import struct
import json
import os

# Configuration
HEX_FILE_PATH = r'c:\git\training_99\reverse_engineering_ref\decompiled\004063e4_hex'
OUTPUT_JSON_PATH = r'c:\git\training_99\doc\game_ranking.json'
OUTPUT_TXT_PATH = r'c:\git\training_99\doc\game_ranking_dump.txt'
KNOWN_TEXT = "便所掃除" # "Toilet Cleaning" - The anchor for verification

def solve():
    print(f"--- 99.exe Data Extractor ---")
    print(f"Goal: Extract game strings and ranking table using verified keys.")
    
    # 1. Read Hex File
    try:
        with open(HEX_FILE_PATH, 'r') as f:
            full_hex = f.read().replace('\n', '').strip()
    except Exception as e:
        print(f"[!] Error reading file: {e}")
        return

    print(f"File loaded. Length: {len(full_hex)//2} bytes.")

    # 2. Extract Strings (String Pool)
    # Based on analysis, the strings in this specific dump appear as RAW Shift-JIS
    # Separated by 'FF' bytes.
    # The String Pool ends around byte 959 (offset 0x3BF).
    
    # Split by FF separator
    # Note: The original code likely iterates pointer by pointer, but splitting by FF is a robust heuristic for this dump.
    SPLIT_OFFSET = 1918 # 959 * 2 hex chars
    string_data_hex = full_hex[:SPLIT_OFFSET]
    table_data_hex = full_hex[SPLIT_OFFSET:]
    
    raw_parts = string_data_hex.split('FF')
    string_table = []
    
    print(f"\n[+] Extracting Strings...")
    known_text_found_at = -1
    
    for idx, hex_part in enumerate(raw_parts):
        if not hex_part:
            string_table.append("")
            continue
            
        # Cleanup odd lengths
        if len(hex_part) % 2 != 0: hex_part = hex_part[:-1]
        
        try:
            b = bytes.fromhex(hex_part)
            # Strategy: Simply decode Shift-JIS.
            # (If this fails later, we can add the XOR logic toggle here)
            decoded = b.decode("shift_jis") 
            string_table.append(decoded)
            
            if KNOWN_TEXT in decoded:
                known_text_found_at = idx
                print(f"    -> Verification Success: Found '{KNOWN_TEXT}' at index {idx}")
                
        except:
            string_table.append(f"<BAD_STR_{idx}>")

    if known_text_found_at == -1:
        print(f"[!] WARNING: Known text '{KNOWN_TEXT}' not found in string pool. Decryption assumption might be wrong.")
    else:
        print(f"[+] String pool extracted ({len(string_table)} entries). verified.")

    # 3. Extract Ranking Table
    # Starts at byte 959.
    # Format: 8 bytes per entry.
    # [Threshold (4b)] [ID1(1b)] [ID2(1b)] [TitleID_Main(1b)] [TitleID_Suffix(1b)]
    # Analysis shows this section IS XOR'd with 0xFF in the dump.
    
    print(f"\n[+] Extracting Ranking Table (XOR 0xFF mode)...")
    
    rankings = []
    pos = 0
    table_bytes = bytes.fromhex(table_data_hex)
    
    while pos + 8 <= len(table_bytes):
        entry_bytes = table_bytes[pos:pos+8]
        
        # XOR Decrypt
        decrypted = bytes([b ^ 0xFF for b in entry_bytes])
        
        # Unpack: Threshold(4), ID1(1), ID2(1), ID3(1), ID4(1)
        threshold = struct.unpack('<I', decrypted[0:4])[0]
        id1 = decrypted[4]
        id2 = decrypted[5]
        id3 = decrypted[6]
        id4 = decrypted[7]
        
        # Map to strings
        str1 = string_table[id1] if id1 < len(string_table) else ""
        str2 = string_table[id2] if id2 < len(string_table) else ""
        str3 = string_table[id3] if id3 < len(string_table) else ""
        str4 = string_table[id4] if id4 < len(string_table) else ""
        
        # In Game Logic (FUN_00404050):
        # It seems ID1 and ID2 are prefix parts (not always drawn?)
        # ID3 is the Main Title (Big Font)
        # ID4 is the Suffix (Bottom)
        
        full_title = f"{str1}{str2}{str3}{str4}"
        
        # Simple heuristic to stop reading garbage at end of file
        # Modified: Don't break, just log. 
        # The table might have entries out of order or special values.
        if threshold > 2000000000: # Just sanity check for insane integer
             pass
            
        rankings.append({
            "t": threshold,
            "title": full_title,
            "parts": [str1, str2, str3, str4]
        })
        
        # Loop limit safety
        if pos > 4000: break # Increased limit
        pos += 8
        
    print(f"[+] Table extracted ({len(rankings)} entries).")
    
    # 4. Filter and Save
    # Remove obvious garbage
    # Relaxed filter to see if we were missing valid high/low entries
    valid_rankings = [r for r in rankings if r['t'] <= 3600000] # Allow up to an hour?
    
    # Save to JSON for Game
    with open(OUTPUT_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(valid_rankings, f, ensure_ascii=False, indent=2)
    print(f"[+] Saved JSON to: {OUTPUT_JSON_PATH}")
    
    # Save Human Readable Doc
    with open(OUTPUT_TXT_PATH, 'w', encoding='utf-8') as f:
        f.write("--- 99.exe Ranking Data ---\n")
        f.write(f"Generated by tools/reverse_data.py\n")
        f.write(f"Dump verification key: {KNOWN_TEXT}\n\n")
        for r in valid_rankings:
            sec = r['t'] / 1000.0
            f.write(f"Time: {sec:>6.2f}s | Title: {r['title']}\n")
            
    print(f"[+] Saved Report to: {OUTPUT_TXT_PATH}")
    
    # Print Preview
    print("\n--- Preview Top 5 ---")
    for r in valid_rankings[:5]:
        print(f"{r['t']/1000}s: {r['title']}")

if __name__ == "__main__": 
    # The discrepancy (Dump says 29,77,68,81 for 15s; Screenshot says 28,74,68,78)
    # suggests that IDs shift at runtime or based on difficulty.
    # But wait, looking at the code:
    # 29 -> 28 (-1)
    # 77 -> 74 (-3)
    # 68 -> 68 (Same)
    # 81 -> 78 (-3)
    
    # ID 77 is "You" (Prefix 2). ID 74 ("You") is also "You".
    # ID 81 is "Certified as." ID 78 ("Appoint to...") is also a suffix.
    
    # Maybe the game CHOOSES between different prefixes/suffixes randomly?
    # Or based on Difficulty?
    # Let's check FUN_00404050 again.
    
    # It reads IDs from table.
    # It draws lpString (ID1) if not null.
    # It draws lpString_01 (ID2) if not null.
    # It draws lpString_00 (ID3) [Main Title].
    # It draws lpchText   (ID4) [Suffix].
    
    # The IDs in the table seem FIXED (29, 77, 68, 81).
    # If the screenshot shows DIFFERENT strings for the SAME title (68),
    # then the table MUST have different values in memory, OR the logic picks differently.
    
    # Hypothesis: The provided hex dump is from a version where the table layout is [29, 77, 68, 81].
    # But maybe the user screenshot is from a play session where RNG modified the table?
    # No, usually static.
    
    # Let's trust the dump we HAVE, but acknowledge the variation.
    # We will output ALL FOUR strings for the remake to fully match the style causing the "vibe".
    
    solve()
