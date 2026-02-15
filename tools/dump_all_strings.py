import sys
import re

def extract_shift_jis_strings(file_path):
    print(f"Opening binary: {file_path}")
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
    except FileNotFoundError:
        print("File not found.")
        return

    # Basic strategy:
    # Scan for sequences of bytes that are valid Shift-JIS or ASCII characters.
    # Min length: 4
    
    # Valid byte ranges for SJIS:
    # ASCII: 0x20 - 0x7E
    # 1st byte: 0x81-0x9F, 0xE0-0xFC
    # 2nd byte: 0x40-0x7E, 0x80-0xFC
    # Half-width kana: 0xA1-0xDF
    
    current_string = bytearray()
    found_strings = []
    
    def is_valid_sjis_first(b):
        return (0x81 <= b <= 0x9F) or (0xE0 <= b <= 0xFC)
        
    def is_valid_sjis_second(b):
        return (0x40 <= b <= 0x7E) or (0x80 <= b <= 0xFC)
        
    def is_ascii(b):
        return (0x20 <= b <= 0x7E) or (b in [0x09, 0x0A, 0x0D]) # Tab, LF, CR

    start_offset = 0
    i = 0
    while i < len(data):
        b = data[i]
        
        # Check for multi-byte SJIS start
        if is_valid_sjis_first(b) and i + 1 < len(data):
            b2 = data[i+1]
            if is_valid_sjis_second(b2):
                if not current_string:
                    start_offset = i
                current_string.append(b)
                current_string.append(b2)
                i += 2
                continue
        
        # Check for ASCII/Half-width
        if is_ascii(b) or (0xA1 <= b <= 0xDF):
            if not current_string:
                start_offset = i
            current_string.append(b)
            i += 1
            continue
            
        # If we hit invalid byte, check if we accumulated enough
        if len(current_string) >= 4:
            try:
                # Attempt decode
                decoded = current_string.decode('shift_jis')
                # Filter noise: strings heavily populated with weird symbols
                if any(ord(c) > 127 for c in decoded) or len(decoded) > 3:
                     # Clean up newlines for printing
                     clean_str = decoded.replace('\r', '').replace('\n', '')
                     print(f"0x{start_offset:X}: {clean_str}")
            except:
                pass
        
        current_string = bytearray()
        i += 1

if __name__ == "__main__":
    extract_shift_jis_strings(r"C:\git\training_99\raw\99.exe")
