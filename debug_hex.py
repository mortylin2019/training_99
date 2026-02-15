import sys

def inspect_hex():
    try:
        with open(r'c:\git\training_99\reverse_engineering_ref\decompiled\004063e4_hex', 'r') as f:
            content = f.read().replace('\n', '').strip()
    except Exception as e:
        print(f"Error: {e}")
        return

    print(f"Total Bytes: {len(content)//2}")
    
    # Check what is at offset 959 (Table Start)
    start = 959 * 2
    # Show 100 bytes from there
    chunk = content[start:start+200]
    print(f"Hex at offset 959: {chunk}")
    
    # Check for 00 vs FF separators in the string area (start of file)
    print(f"String Area Sample: {content[:100]}")
    
    # Check frequency of FF in string area
    msg_area = content[:start]
    ff_count = msg_area.count('FF')
    zz_count = msg_area.count('00')
    print(f"String Area (0-959): 'FF' count={ff_count}, '00' count={zz_count}")

if __name__ == "__main__":
    inspect_hex()
