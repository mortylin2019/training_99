import os
import re

# Source file path
SOURCE_FILE = r"c:\git\training_99\reverse_engineering_ref\decompiled\99.exe.c"
# Output directory
OUTPUT_DIR = r"c:\git\training_99\reverse_engineering_ref\python_breakdown"

# Function map based on analysis
# (Function Name, Description / Output Filename)
FUNCTION_MAP = {
    "FUN_004042f0": "main_loop_state_machine.c",
    "FUN_00403ac0": "stage_1_start_screen.c",
    "FUN_00402fbc": "stage_2_game_entity_loop.c",
    "FUN_004046cc": "input_handling_and_timer.c",
    "FUN_00404050": "stage_3_dead_ranking_summary.c",
    "FUN_00403d84": "stage_4_game_over_display.c",
    "FUN_00402e88": "bullet_mechanics.c",
    "FUN_00402000": "rng_helper.c",
    "FUN_00404660": "game_initialization.c",
    "WinMain": "entry_point.c" 
}

def extract_functions(source_path, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    with open(source_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Generic extraction for void FUN_XXXX or similar
    # This regex looks for start of function 'void FUN_...' until the start of next function or end of file
    # It's a heuristic, but often works for Hex-Rays output if it's well structured.
    
    # However, since the file is large, we can loop through lines to find start/end.
    
    lines = content.split('\n')
    current_func = None
    func_content = []
    
    # Store global variables and types (header)
    header_content = []
    in_header = True
    
    for line in lines:
        # Detect function start
        # Patterns like: "void FUN_004042f0(void)" or "int __stdcall WinMain(...)"
        # We look for the exact names in our map
        
        match = None
        for func_name in FUNCTION_MAP.keys():
            if line.startswith(f"void {func_name}") or line.startswith(f"int {func_name}") or f" {func_name}(" in line:
                # Check if it's a definition (contains { at end or next line)
                # But typically decompilers put "void FUN_...(void)" then "{"
                if ";" not in line: # Skip prototypes
                    match = func_name
                    break
        
        if match:
            # If we were processing a function, save it (though we only care about specific ones)
            if current_func and current_func in FUNCTION_MAP:
                save_file(output_dir, FUNCTION_MAP[current_func], func_content)
            
            # Start new function
            current_func = match
            func_content = [line]
            in_header = False
            continue
            
        if in_header:
            header_content.append(line)
        elif current_func:
            func_content.append(line)
            # We don't easily know where it ends without parsing braces, 
            # but we can assume it ends when the next identified function starts
            # or we can simple dump everything until the next match.

    # Save the last function if it was one we wanted
    if current_func and current_func in FUNCTION_MAP:
        save_file(output_dir, FUNCTION_MAP[current_func], func_content)
        
    # Save header/globals
    save_file(output_dir, "00_globals_and_types.c", header_content)
    
    print(f"Breakdown complete. Files saved to {output_dir}")

def save_file(folder, filename, lines):
    path = os.path.join(folder, filename)
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f"Generated: {filename}")

if __name__ == "__main__":
    extract_functions(SOURCE_FILE, OUTPUT_DIR)
