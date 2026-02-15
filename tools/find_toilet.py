
import struct

# The full hex dump from the user's file
hex_path = r'c:\git\training_99\reverse_engineering_ref\decompiled\004063e4_hex'

with open(hex_path, 'r') as f:
    full_hex = f.read().strip()

# We are looking for the "Toilet Cleaning" entry.
# IDs: Prefix1=63(0x3F), Prefix2=75(0x4B), Title=70(0x46), Suffix=73(0x49)
# Encrypted (XOR FF):
# 63 -> C0
# 75 -> B4
# 70 -> B9
# 73 -> B6

# The structure is [Threshold 4B] [ID1] [ID2] [ID3] [ID4]
# So we are looking for the byte sequence: C0 B4 B9 B6
# Or maybe the order is specific.
# Let's search for the Title ID (B9) in the latter half of the 8-byte blocks.

data = bytes.fromhex(full_hex)
start_offset = 1918 # Table starts here

print(f"Searching for Toilet Cleaning pattern (C0 B4 B9 B6) starting at {start_offset}...")

found = False
for i in range(start_offset, len(data) - 4):
    window = data[i:i+4]
    # Check for the pattern C0 B4 B9 B6
    if window == bytes([0xC0, 0xB4, 0xB9, 0xB6]):
        print(f"FOUND EXACT MATCH at offset {i}!")
        # The threshold should be the 4 bytes before this
        entry_start = i - 4
        t_bytes = data[entry_start:entry_start+4]
        t_dec = bytes([b ^ 0xFF for b in t_bytes])
        t_val = struct.unpack('<I', t_dec)[0]
        print(f"Threshold: {t_val} (Entry Start: {entry_start})")
        found = True

if not found:
    print("Exact match not found. Searching partials...")
    # Maybe prefix is optional or different?
    # Search for just Title=70 (B9) and Suffix=73 (B6) -> B9 B6 at end
    for i in range(start_offset, len(data), 8):
        # Bytes 6 and 7 of the entry are MainTitle and Suffix usually
        # But wait, looking at my previous extraction:
        # id3 = decrypted[6] (Main Title)
        # id4 = decrypted[7] (Suffix)
        
        # So we expect [?? ?? B9 B6] at the end of the 8 bytes.
        chunk = data[i:i+8]
        if len(chunk) < 8: continue
        
        dec = bytes([b ^ 0xFF for b in chunk])
        
        # Print if Title is 70
        if dec[6] == 70:
            t = struct.unpack('<I', dec[0:4])[0]
            print(f"Offset {i}: Threshold={t}, IDs=[{dec[4]}, {dec[5]}, {dec[6]}, {dec[7]}]")

