import sys
import struct
import json

def process():
    try:
        with open(r'c:\git\training_99\reverse_engineering_ref\decompiled\004063e4_hex', 'r') as f:
            full_hex = f.read().replace('\n', '').strip()
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    # --- Part 1: Extract Strings ---
    # Offset 0 to 959 (1918 hex chars)
    string_hex = full_hex[:1918]
    
    # The file uses FF as separator for PLAIN TEXT strings
    hex_parts = string_hex.split('FF')
    
    strings = []
    
    print(f"Found {len(hex_parts)} string segments.")
    
    for i, part in enumerate(hex_parts):
        # We keep ALL entries to maintain index alignment
        if len(part) == 0:
            strings.append("")
            continue
            
        # Handle odd length (just in case)
        if len(part) % 2 != 0: part = part[:-1]
        
        try:
            b = bytes.fromhex(part)
            # Try decode
            text = b.decode("shift_jis")
            strings.append(text)
        except:
            strings.append(f"<BAD_DATA_IDX_{i}>")

    # --- Part 2: Extract Ranking Table ---
    # Starts at byte 959 (hex 1918)
    table_hex = full_hex[1918:]
    
    rankings = []
    
    # Process in 8-byte chunks (16 hex chars)
    pos = 0
    while pos + 16 <= len(table_hex):
        chunk = table_hex[pos:pos+16]
        raw_bytes = bytes.fromhex(chunk)
        
        # XOR with 0xFF to decrypt
        decrypted = bytes([b ^ 0xFF for b in raw_bytes])
        
        # Unpack: Threshold (I), ID1 (B), ID2 (B), ID3 (B), ID4 (B)
        threshold = struct.unpack('<I', decrypted[0:4])[0]
        id1 = decrypted[4]
        id2 = decrypted[5]
        id3 = decrypted[6]
        id4 = decrypted[7]
        
        # Interpret
        # ID3 seems to be the main title index
        # ID4 seems to be a suffix or secondary title
        
        title1 = strings[id3] if id3 < len(strings) else ""
        title2 = strings[id4] if id4 < len(strings) else ""
        
        entry = {
            "threshold_ms": threshold,
            "id3": id3,
            "id4": id4,
            "title_combined": f"{title1}{title2}"
        }
        
        rankings.append(entry)
        
        # Stop condition: 
        # If threshold is 0 (and we aren't at start), or crazy high/low unexpectedly?
        # The first entry was 180,000.
        # If we see 0, it might be the end.
        if threshold == 0:
             # Check if it really looks like the end (all 0s or FFs originally)
             pass
        
        pos += 16
        if pos > 4000: break # Safety break

    # Filter out entries with invalid threshold (e.g. 0 at the end)
    # Actually 0 threshold might be "default" or "game over immediately".
    # But typically table ends with 0.
    
    valid_rankings = [r for r in rankings if r['threshold_ms'] > 0 and r['threshold_ms'] < 300000]
    
    print(f"Extracted {len(valid_rankings)} ranking entries.")
    
    # Output content for review
    output_lines = []
    for r in valid_rankings:
        line = f"Time: {r['threshold_ms']/1000:6.2f}s | Title: {r['title_combined']} (IDs: {r['id3']}, {r['id4']})"
        output_lines.append(line)
        print(line)

    with open(r'c:\git\training_99\doc\game_ranking.txt', 'w', encoding='utf-8') as f:
        f.write("\n".join(output_lines))
        
    # Also save JSON for game
    with open(r'c:\git\training_99\flask_app\static\rankings.json', 'w', encoding='utf-8') as f:
        json.dump(valid_rankings, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    process()
