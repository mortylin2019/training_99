import os
import re

# Directory containing the broken down files
SOURCE_DIR = r"c:\git\training_99\reverse_engineering_ref\python_breakdown"

# Mapping of Symbols to Readable Names
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
    "FUN_004025b0": "Entity_UpdateMovement", # Inferred from context in Game_EntityLoop or similar
    "FUN_00402a30": "Entity_Type1_Homing",
    "FUN_00402978": "Entity_Type2_Bounce",
    
    # Global Variables (Inferred from previous analysis)
    "DAT_00406d88": "G_Score_Time",
    "DAT_00406da4": "G_CurrentTime_Tick",
    "DAT_00406d94": "G_GameStartTime",
    "DAT_00406da8": "G_CurrentBulletCount",   # Increases to 300
    "DAT_00406dc0": "G_DifficultyMode",       # 0=Normal?, 2=Hard?
    "DAT_00406d8c": "G_ScoreMultiplier",      # 0, 10, 12, 16 etc
    "DAT_00406e10": "G_EntityArray",          # Structure array
    "DAT_00406a00": "G_HeapMemory",
    "DAT_004069e4": "G_BackBufferDC",
    "DAT_004069e0": "G_SpriteDC",     
    "DAT_00406d80": "G_GameOverFlag",
    "DAT_00406d74": "G_GameState",            # 0=Title, 1=Play, 2=Dead?
    "DAT_00406d84": "G_PauseFlag",
    "DAT_00406dcc": "G_HighPriorityMode",
    "DAT_00406dbc": "G_NextBulletPattern",    # Modulo 7
    "DAT_00406dfc": "G_NextSpawnTime",
    "DAT_00406e00": "G_NextPatternTime",
    "DAT_00406e04": "G_SomePatternCounter",   # Decrements
    "DAT_00406e08": "G_PatternTimer2",
    "DAT_00406e0c": "G_PatternCounter",
    "DAT_00406db0": "G_PatternDuration",
    "_DAT_00406db0": "G_PatternDuration",
    "DAT_00406db4": "G_ActiveEntityCount",
    "DAT_00406db8": "G_TotalEntitiesSpawned", # Accumulates
    "DAT_00406d6c": "G_PlayerX",
    "DAT_00406d70": "G_PlayerY",
    "DAT_00406d98": "G_DeathTime",
    "DAT_00406d90": "G_IsGameRunning",        # 1 if running?
    "DAT_00406d78": "G_SubState",             # Sub-state within GameState
    "DAT_00406d7c": "G_InputState",           # Bitmask?
}

def translate_files(directory):
    print(f"Translating files in {directory}...")
    
    for filename in os.listdir(directory):
        if not filename.endswith(".c") and not filename.endswith(".h"):
            continue
            
        filepath = os.path.join(directory, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        old_content = content
        
        # Sort items by length (descending) to avoid partial replacements 
        # (e.g. replacing VAR_1 before VAR_10)
        sorted_map = sorted(SYMBOL_MAP.items(), key=lambda x: len(x[0]), reverse=True)
        
        for original, reuse in sorted_map:
            # Use regex to replace only whole words to avoid replacing substrings incorrectly
            # e.g. defined variables inside comments or similar strings might be tricky, 
            # but usually C identifiers are distinct.
            
            # This regex matches the symbol if it's not preceded or followed by alphanumeric chars/underscores
            pattern = r'(?<![a-zA-Z0-9_])' + re.escape(original) + r'(?![a-zA-Z0-9_])'
            content = re.sub(pattern, reuse, content)
            
        if content != old_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated {filename}")
        else:
            print(f"No changes in {filename}")

if __name__ == "__main__":
    translate_files(SOURCE_DIR)
