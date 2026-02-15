import sys
import struct

def extract():
    try:
        with open(r'c:\git\training_99\reverse_engineering_ref\decompiled\004063e4_hex', 'r') as f:
            hex_str = f.read().replace('\n', '').strip()
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    # Offset from 004063e4 to 004067a3 is 0x3BF = 959 bytes.
    # Hex string uses 2 chars per byte.
    start_offset = 959
    hex_start = start_offset * 2
    
    if len(hex_str) <= hex_start:
        print(f"Hex dump too short. Length: {len(hex_str)/2} bytes. Needed > 959.")
        return

    print("--- Ranking Table (Threshold | ID1 | ID2 | ID3 | ID4) ---")
    print("ID1/2 might be unused. ID3=Title, ID4=Suffix")
    
    # Process 8 bytes (16 hex chars) at a time
    current_pos = hex_start
    while current_pos + 16 <= len(hex_str):
        chunk = hex_str[current_pos:current_pos+16]
        data = bytes.fromhex(chunk)
        
        # Unpack: uint32 (LE), byte, byte, byte, byte
        threshold = struct.unpack('<I', data[0:4])[0]
        id1 = data[4]
        id2 = data[5]
        id3 = data[6]
        id4 = data[7]
        
        print(f"Score < {threshold}: [{id1}, {id2}, {id3}, {id4}]")
        
        # Heuristic stop: reasonable upper bound for score? 
        # TimeGetTime is ms. 60 sec = 60000. 
        # If threshold jumps to huge number or 0 (if end of table behavior isn't infinite), we stop.
        # But loop condition is `while (score < threshold)`.
        # Usually checking linearly. 
        # If threshold is 0 and it's sorted, we might be at end or start?
        # Actually existing games use MAX_INT for last entry.
        
        current_pos += 16
        
        if threshold > 10000000: # 10000 seconds
            break

if __name__ == "__main__":
    extract()
