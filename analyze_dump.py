
import struct

def analyze():
    # Load strings first to have the mapping
    try:
        with open(r'c:\git\training_99\reverse_engineering_ref\decompiled\004063e4_hex', 'r') as f:
            full_hex = f.read().replace('\n', '').strip()
    except Exception as e:
        print(f"Error reading dump: {e}")
        return

    string_hex = full_hex[:1918]
    hex_parts = string_hex.split('FF')
    strings = []
    for part in hex_parts:
        if len(part) % 2 != 0: part = part[:-1]
        try:
            b = bytes.fromhex(part)
            text = b.decode("shift_jis")
            strings.append(text)
        except:
            strings.append("<BAD>")
            
    # Now look at the ranking table area
    table_hex = full_hex[1918:]
    print(f"Total table hex length: {len(table_hex)}")
    
    pos = 0
    while pos + 16 <= len(table_hex):
        chunk = table_hex[pos:pos+16]
        raw_bytes = bytes.fromhex(chunk)
        decrypted = bytes([b ^ 0xFF for b in raw_bytes])
        
        threshold = struct.unpack('<I', decrypted[0:4])[0]
        id1 = decrypted[4]
        id2 = decrypted[5]
        id3 = decrypted[6]
        id4 = decrypted[7]
        
        # Check if ID 10 (Suteki) is present
        if id3 == 10 or id4 == 10:
            print(f"Found ID 10 at threshold {threshold}: ID3={id3} ('{strings[id3] if id3 < len(strings) else ''}'), ID4={id4} ('{strings[id4] if id4 < len(strings) else ''}')")
            
        pos += 16

if __name__ == "__main__":
    analyze()
