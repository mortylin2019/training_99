import os
import re
import csv

# Source file settings
SOURCE_FILE = r"c:\git\training_99\reverse_engineering_ref\decompiled\99.exe.c"
STRING_DUMP_FILE = r"c:\git\training_99\reverse_engineering_ref\decompiled\004063e4_hex"
MANUAL_STRINGS_FILE = r"c:\git\training_99\reverse_engineering_ref\decompiled\manual_strings.csv" # New CSV file
OUTPUT_DIR = r"c:\git\training_99\reverse_engineering_ref\python_breakdown"

# Base address for the string dump
STRING_BASE_ADDRESS = 0x004063e4

# --- Function Breakdown Configuration ---
FUNCTION_MAP = {
    "FUN_004042f0": "MainLoop_StateMachine.c",
    "FUN_00403ac0": "Stage1_StartScreen.c",
    "FUN_00402fbc": "Stage2_GameEntityLoop.c",
    "FUN_004046cc": "Sys_InputTimerUpdate.c",
    "FUN_00404050": "Stage3_DeadRankingSummary.c",
    "FUN_00403d84": "Stage4_GameOverDisplay.c",
    "FUN_00402e88": "Bullet_Mechanics.c",
    "FUN_00402000": "Util_Random.c",
    "FUN_00404660": "Game_Init.c",
    "FUN_004025b0": "Entity_UpdateMovement.c",
    "FUN_00402a30": "Entity_Type1_Homing.c",
    "FUN_00402978": "Entity_Type2_Bounce.c",
    "WinMain": "entry_point.c" 
}

# --- Symbol Translation Configuration ---
SYMBOL_MAP = {
    # Functions
    "FUN_004042f0": "MainLoop_StateMachine",
    "FUN_00403ac0": "DrawStartScreen",
    "FUN_00402fbc": "Game_EntityLoop",
    "FUN_004046cc": "Sys_InputTimerUpdate",
    "FUN_00404050": "Game_CalculateRanking",
    "FUN_00403d84": "DrawGameOver",
    "FUN_00402e88": "Entity_SpawnBullet",
    "FUN_00402000": "Util_Random",
    "FUN_00404660": "Game_Init",
    "FUN_004025b0": "Entity_UpdateMovement",
    "FUN_00402a30": "Entity_Type1_Homing",
    "FUN_00402978": "Entity_Type2_Bounce",
    
    # Global Variables
    "DAT_00406d88": "G_Score_Time",
    "DAT_00406da4": "G_CurrentTime_Tick",
    "DAT_00406d94": "G_GameStartTime",
    "DAT_00406da8": "G_CurrentBulletCount",   
    "DAT_00406dc0": "G_DifficultyMode",       
    "DAT_00406d8c": "G_ScoreMultiplier",      
    "DAT_00406e10": "G_EntityArray",          
    "DAT_00406a00": "G_HeapMemory",
    "DAT_004069e4": "G_BackBufferDC",
    "DAT_004069e0": "G_SpriteDC",     
    "DAT_00406d80": "G_GameOverFlag",
    "DAT_00406d74": "G_GameState",            
    "DAT_00406d84": "G_PauseFlag",
    "DAT_00406dcc": "G_HighPriorityMode",
    "DAT_00406dbc": "G_NextBulletPattern",    
    "DAT_00406dfc": "G_NextSpawnTime",
    "DAT_00406e00": "G_NextPatternTime",
    "DAT_00406e04": "G_SomePatternCounter",   
    "DAT_00406e08": "G_PatternTimer2",
    "DAT_00406e0c": "G_PatternCounter",
    "DAT_00406db0": "G_PatternDuration",
    "_DAT_00406db0": "G_PatternDuration",
    "DAT_00406db4": "G_ActiveEntityCount",
    "DAT_00406db8": "G_TotalEntitiesSpawned", 
    "DAT_00406d6c": "G_PlayerX",
    "DAT_00406d70": "G_PlayerY",
    "DAT_00406d98": "G_DeathTime",
    "DAT_00406d90": "G_IsGameRunning",        
    "DAT_00406d78": "G_SubState",             
    "DAT_00406d7c": "G_InputState",           
}

# --- Utils ---
def parse_manual_strings(csv_path):
    """
    Parses manual strings CSV.
    Expected format: Location (hex), String_Value, ...
    Returns a dictionary: { address (int) : string_content (str) }
    """
    print(f"Parsing manual strings from {csv_path}...")
    manual_map = {}
    if not os.path.exists(csv_path):
        print(f"Warning: Manual strings file not found at {csv_path}")
        return manual_map

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None) # Skip header if present, or robust check
            
            for row in reader:
                if not row or len(row) < 2:
                    continue
                    
                loc_str = row[0].strip()
                val_str = row[1].strip()
                
                # Check for comment/header
                if loc_str.lower().startswith('location') or loc_str.startswith('#'):
                     continue

                try:
                    addr = int(loc_str, 16)
                    manual_map[addr] = val_str
                except ValueError:
                    pass
    except Exception as e:
        print(f"Warning: Failed to parse manual strings: {e}")
    
    print(f"Found {len(manual_map)} manual strings.")
    return manual_map

def parse_hex_strings(hex_path, base_address):
    """
    Parses the hex dump to find strings.
    Returns a dictionary: { address (int) : string_content (str) }
    """
    print(f"Parsing strings from {hex_path}...")
    string_map = {}
    try:
        with open(hex_path, 'r') as f:
            hex_content = f.read().strip().replace('\n', '')
        
        data = bytes.fromhex(hex_content)
        
        current_bytes = bytearray()
        start_offset = 0
        in_string = False
        
        for i, byte in enumerate(data):
            # 0xFF / 0x00 delimiters
            if byte == 0xFF or byte == 0x00:
                if in_string:
                    try:
                        decoded = current_bytes.decode('shift_jis')
                        if decoded and len(decoded) > 1: # Filter tiny garbage
                            addr = base_address + start_offset
                            string_map[addr] = decoded
                    except UnicodeDecodeError:
                        pass
                    current_bytes = bytearray()
                    in_string = False
            else:
                if not in_string:
                    start_offset = i
                    in_string = True
                current_bytes.append(byte)
                
        # Handle last one
        if in_string:
             try:
                decoded = current_bytes.decode('shift_jis')
                if decoded:
                    addr = base_address + start_offset
                    string_map[addr] = decoded
             except: pass
             
    except Exception as e:
        print(f"Warning: Failed to parse strings: {e}")
        
    print(f"Found {len(string_map)} strings.")
    return string_map

def apply_symbol_translations(content):
    """Replaces variable/function names with readable ones."""
    sorted_map = sorted(SYMBOL_MAP.items(), key=lambda x: len(x[0]), reverse=True)
    for original, reuse in sorted_map:
        pattern = r'(?<![a-zA-Z0-9_])' + re.escape(original) + r'(?![a-zA-Z0-9_])'
        content = re.sub(pattern, reuse, content)
    return content

def apply_string_translations(content, string_map):
    """
    Replaces references to string addresses with the actual string content in comments or inline.
    """
    # Merge manual strings first
    try:
        manual_map = parse_manual_strings(MANUAL_STRINGS_FILE)
        string_map.update(manual_map)
    except Exception as e:
        print(f"Warning: Could not parse manual strings: {e}")

    sorted_addrs = sorted(string_map.keys(), reverse=True)
    
    for addr in sorted_addrs:
        s_content = string_map[addr]
        if not s_content: continue
        
        # Escape string for C comment
        s_content_safe = s_content.replace('\n', ' ').replace('\r', '').replace('"', "'")
        
        # Pattern 1: DAT_00406405 or lpchText_00406405
        var_name = f"DAT_{addr:08x}"
        var_name_2 = f"lpchText_{addr:08x}"
        
        content = re.sub(
            rf"&?{var_name}(?![0-9a-fA-F])",
            lambda match: f'{match.group(0)} /* "{s_content_safe}" */',
            content
        )

        content = re.sub(
            rf"&?{var_name_2}(?![0-9a-fA-F])",
            lambda match: f'{match.group(0)} /* "{s_content_safe}" */',
            content
        )
        
        # Case B: (LPCSTR)0x406405
        hex_val = f"0x{addr:x}"
        # We need to escape special regex chars in hex_val if any (unlikely for hex)
        
        content = re.sub(
            rf"\(LPCSTR\){hex_val}(?![0-9a-fA-F])",
            lambda match: f'{match.group(0)} /* "{s_content_safe}" */',
            content,
            flags=re.IGNORECASE
        )

    return content

def save_file(folder, filename, lines):
    path = os.path.join(folder, filename)
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f"Generated: {filename}")

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    # 1. Parse Strings
    string_map = parse_hex_strings(STRING_DUMP_FILE, STRING_BASE_ADDRESS)

    # 2. Read Source
    with open(SOURCE_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        full_content = f.read()

    lines = full_content.split('\n')
    current_func = None
    func_content = []
    
    # Store global variables and types (header)
    header_content = []
    in_header = True
    
    # 3. Process Line by Line (Extraction)
    for line in lines:
        # Detect function start
        match = None
        for func_name in FUNCTION_MAP.keys():
            if line.startswith(f"void {func_name}") or line.startswith(f"int {func_name}") or f" {func_name}(" in line:
                if ";" not in line: 
                    match = func_name
                    break
        
        if match:
            # Save previous function
            if current_func and current_func in FUNCTION_MAP:
                processed_content = '\n'.join(func_content)
                processed_content = apply_symbol_translations(processed_content)
                processed_content = apply_string_translations(processed_content, string_map)
                save_file(OUTPUT_DIR, FUNCTION_MAP[current_func], processed_content.split('\n'))
            
            current_func = match
            func_content = [line]
            in_header = False
            continue
            
        if in_header:
            header_content.append(line)
        elif current_func:
            func_content.append(line)

    # Save last function
    if current_func and current_func in FUNCTION_MAP:
        processed_content = '\n'.join(func_content)
        processed_content = apply_symbol_translations(processed_content)
        processed_content = apply_string_translations(processed_content, string_map)
        save_file(OUTPUT_DIR, FUNCTION_MAP[current_func], processed_content.split('\n'))
        
    # Save header
    header_processed = '\n'.join(header_content)
    header_processed = apply_symbol_translations(header_processed)
    # Header usually doesn't have string refs but good to be consistent
    save_file(OUTPUT_DIR, "00_globals_and_types.c", header_processed.split('\n'))
    
    print(f"Breakdown and Translation complete. Files in {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
