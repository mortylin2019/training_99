import sys
import os

def analyze_strings(file_path):
    print(f"Reading file: {file_path}")
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return

    with open(file_path, 'rb') as f:
        data = f.read()

    print(f"File size: {len(data)} bytes")

    # Shift-JIS strings
    # "Enter" (ASCII) -> 45 6E 74 65 72
    # Just search for "Enter" first as reliable anchor
    target_bytes = b'Enter'
    
    print("\n--- Searching for 'Enter' ---")
    
    # 1. Plain
    idx = data.find(target_bytes)
    if idx != -1:
        print(f"[PLAIN FOUND] 'Enter' at offset 0x{idx:X}")
        # Dump surrounding
        start = max(0, idx - 10)
        end = min(len(data), idx + 20)
        print(f"Context: {data[start:end]}")
    else:
        print("[PLAIN NOT FOUND]")

    # 2. XOR Search (Single Byte)
    print("\n--- Searching for XORed Patterns (Byte-by-byte) ---")
    
    # Brute force ALL chunks of length 10 looking for high entropy text? 
    # Or just look for the known string again.
    
    # Let's try searching for the Shift-JIS bytes of "特訓" (Tokkun - Training)
    # 特: 93 42
    # 訓: 8C 56
    tokkun_bytes = bytes([0x93, 0x42, 0x8C, 0x56])
    
    for xor_key in range(1, 256):
        encoded_tokkun = bytes([b ^ xor_key for b in tokkun_bytes])
        idx_xor = data.find(encoded_tokkun)
        if idx_xor != -1:
            print(f"[XOR 0x{xor_key:02X} FOUND] '特訓' at offset 0x{idx_xor:X}")
            
            # Decrypt full string around it
            start = max(0, idx_xor - 20)
            end = min(len(data), idx_xor + 40)
            chunk = data[start:end]
            decoded = bytes([b ^ xor_key for b in chunk])
            try:
                print(f"Decoded Context: {decoded.decode('shift_jis', errors='replace')}")
            except:
                pass

    # 3. Analyze Code Section for String Usage
    # If standard PE, text section is usually .text.
    # We can try to dump all strings with length > 4 that serve as decent Shift-JIS

if __name__ == "__main__":
    analyze_strings(r"C:\git\training_99\raw\99.exe")
