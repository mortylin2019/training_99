
import struct

def main():
    file_path = r"c:\git\training_99\reverse_engineering_ref\decompiled\004063e4_hex"
    
    with open(file_path, "r") as f:
        hex_data = f.read().strip()
    
    # Remove XML/markdown wrappers if mistakenly included (read_file output might, but file on disk shouldn't)
    # The user provided file content seems to be just hex characters, but let's be safe.
    # Looking at previous read_file output:
    # 9347914F...
    
    # Just in case there are newlines
    hex_data = hex_data.replace("\n", "").replace("\r", "")

    try:
        data = bytes.fromhex(hex_data)
    except ValueError as e:
        print(f"Error parsing hex: {e}")
        return

    start_addr = 0x004063e4
    current_addr = start_addr
    
    current_string_bytes = bytearray()
    string_start_addr = start_addr
    
    mappings = []
    
    i = 0
    while i < len(data):
        b = data[i]
        
        # Check for delimiters 0xFF or 0x00
        # Sometimes 0xFF is used, sometimes 0x00.
        # Based on the visual inspection of the hex dump provided in the prompt:
        # 9347...82E9 FF 6C59...
        # It seems 0xFF is a separator.
        
        if b == 0xFF or b == 0x00:
            if len(current_string_bytes) > 0:
                try:
                    # Attempt decode
                    decoded = current_string_bytes.decode("shift_jis")
                    mappings.append((string_start_addr, decoded))
                except UnicodeDecodeError:
                    # If it fails, maybe just show hex or try utf-8
                    # mappings.append((string_start_addr, f"<BAD DECODE: {current_string_bytes.hex()}>"))
                    pass # Ignore garbage
                
                current_string_bytes = bytearray()
            
            # If we hit a delimiter, the next string starts at i+1 (which corresponds to current_addr + 1)
            # But we need to be careful if there are multiple delimiters in a row.
            
            string_start_addr = start_addr + i + 1
        else:
            current_string_bytes.append(b)
            
        i += 1
        
    # Check if there is a leftover string at the end
    if len(current_string_bytes) > 0:
        try:
            decoded = current_string_bytes.decode("shift_jis")
            mappings.append((string_start_addr, decoded))
        except:
            pass

    for addr, s in mappings:
        print(f"0x{addr:08X}: {s}")

if __name__ == "__main__":
    main()
