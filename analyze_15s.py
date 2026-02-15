if __name__ == "__main__":
    import sys, struct
    try:
        with open(r'c:\git\training_99\reverse_engineering_ref\decompiled\004063e4_hex', 'r') as f:
            full_hex = f.read().replace('\n', '').strip()
    except Exception as e:
        print(e)
        sys.exit()

    # Table starts at 959
    print("Scanning entire table for ID 68 (Bullet Gatherer)...")
    
    pos = 1918
    while pos + 16 <= len(full_hex):
        chunk = full_hex[pos:pos+16]
        raw_bytes = bytes.fromhex(chunk)
        decrypted = bytes([b ^ 0xFF for b in raw_bytes])
        
        threshold = struct.unpack('<I', decrypted[0:4])[0]
        
        b4 = decrypted[4]
        b5 = decrypted[5]
        b6 = decrypted[6]
        b7 = decrypted[7]
        
        # Check for ID 68 as *Main* title (ID3=b6)
        if b6==68:
             print(f"FOUND Main Title 68: Threshold {threshold} | IDs {b4},{b5},{b6},{b7}")
             
        pos += 16