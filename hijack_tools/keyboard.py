"""
Centralized Input Mapping for 99.exe
Based on empirical testing (input_test.py).

Mappings:
1: LEFT
2: UP (Decreases Y)
4: DOWN (Increases Y)
8: RIGHT
"""

# Base Directions
KEY_STOP  = 0
KEY_LEFT  = 1
KEY_UP    = 2
KEY_DOWN  = 4
KEY_RIGHT = 8

# Diagonals
KEY_UP_LEFT    = KEY_UP | KEY_LEFT       # 3
KEY_UP_RIGHT   = KEY_UP | KEY_RIGHT      # 10
KEY_DOWN_LEFT  = KEY_DOWN | KEY_LEFT     # 5
KEY_DOWN_RIGHT = KEY_DOWN | KEY_RIGHT    # 12

# Map for Logging / Debugging
KEY_NAMES = {
    KEY_STOP: "STOP",
    KEY_LEFT: "LEFT",
    KEY_RIGHT: "RIGHT",
    KEY_UP: "UP",
    KEY_DOWN: "DOWN",
    KEY_UP_LEFT: "UP-LEFT",
    KEY_DOWN_LEFT: "DOWN-LEFT",
    KEY_UP_RIGHT: "UP-RIGHT",
    KEY_DOWN_RIGHT: "DOWN-RIGHT"
}

def get_key_name(bits):
    return KEY_NAMES.get(bits, f"UNKNOWN({bits})")
