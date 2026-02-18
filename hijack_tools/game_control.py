import ctypes
import time
import subprocess
import os
import struct
from dataclasses import dataclass

# Windows Constants
PROCESS_ALL_ACCESS = 0x1F0FFF
@dataclass
class Bullet:
    raw_x: int
    raw_y: int
    angle_index: int  # Offset 0x08 - Direction for Type 0/1/3
    active: int       # Offset 0x09
    type: int         # Offset 0x0A (0: Normal, 1: Homing, 2: Bounce, 3: Accel)
    timer: int        # Offset 0x0B
    index: int        # Offset 0x0C
    vx: int           # Offset 0x0D - Direct speed for Type 2
    vy: int           # Offset 0x0E - Direct speed for Type 2

    @property
    def x(self) -> int:
        return (self.raw_x >> 6) - 4

    @property
    def y(self) -> int:
        return (self.raw_y >> 6) - 4

    def __repr__(self):
        # Type 2 uses simple vx/vy, others use angle_index to look up vectors
        move_info = f"v={self.vx},{self.vy}" if self.type == 2 else f"angle={self.angle_index}"
        return f"({self.x},{self.y},T{self.type},{move_info})"

WM_KEYDOWN = 0x100
WM_KEYUP = 0x101
VK_LEFT = 0x25
VK_UP = 0x26
VK_RIGHT = 0x27
VK_DOWN = 0x28
VK_RETURN = 0x0D
VK_SPACE = 0x20

# Game Logic Constants (Offsets)
# These are gathered from the reverse engineering analysis
ADDR_PLAYER_X = 0x00406d6c
ADDR_PLAYER_Y = 0x00406d70
ADDR_GAME_STATE = 0x00406d84 # Using G_PauseFlag as it is the real state indicator
ADDR_INPUT_STATE = 0x00406d7c
ADDR_BULLET_COUNT = 0x00406da8
ADDR_ENTITY_ARRAY = 0x00406e10
ENTITY_SIZE = 15 # The game increments entity pointer by 0x0F (15 bytes)

class GameControl:
    def __init__(self, exe_path=r"C:\git\training_99\raw\99.exe"):
        self.exe_path = exe_path
        self.process_handle = None
        self.pid = None
        self.hwnd = None

    def launch_game(self):
        """Launches the game and attaches to its process."""
        print(f"Launching {self.exe_path}...")
        try:
            proc = subprocess.Popen(self.exe_path, cwd=os.path.dirname(self.exe_path))
            self.pid = proc.pid
            time.sleep(1) # Wait for window to initialize
            
            # Find Window
            # Title is '特訓９９' (Japanese for Training 99)
            # We try both fullwidth and normal just in case
            titles = ["特訓９９", "99", "特訓"]
            for title in titles:
                self.hwnd = ctypes.windll.user32.FindWindowW(None, title)
                if self.hwnd:
                    print(f"Found window: {title} (HWND: {self.hwnd})")
                    break
            
            if not self.hwnd:
                # Try finding by class name if known (from analysis: 'TKKN')
                self.hwnd = ctypes.windll.user32.FindWindowW("TKKN", None)
                if self.hwnd:
                    print(f"Found window by class TKKN (HWND: {self.hwnd})")

            # Get process handle
            self.process_handle = ctypes.windll.kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, self.pid)
            if not self.process_handle:
                # If we can't get it by PID from Popen (maybe it spawned another process), try GetWindowThreadProcessId
                pid = ctypes.c_ulong()
                ctypes.windll.user32.GetWindowThreadProcessId(self.hwnd, ctypes.byref(pid))
                self.pid = pid.value
                self.process_handle = ctypes.windll.kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, self.pid)

            if self.process_handle:
                print(f"Attached to process PID: {self.pid}")
                return True
            else:
                print("Failed to attach to process.")
                return False
        except Exception as e:
            print(f"Error launching game: {e}")
            return False

    def read_memory(self, address, size=4):
        """Reads memory from the process."""
        buffer = ctypes.create_string_buffer(size)
        bytes_read = ctypes.c_size_t()
        if ctypes.windll.kernel32.ReadProcessMemory(self.process_handle, address, buffer, size, ctypes.byref(bytes_read)):
            return buffer.raw
        return None

    def read_int(self, address):
        data = self.read_memory(address, 4)
        if data:
            return struct.unpack("<I", data)[0]
        return None

    def get_game_state(self):
        """
        Returns indicator of the current menu/play state.
        0: Title/Start
        1: Playing
        5: Game Over Result
        6: Ranking Summary
        """
        return self.read_int(ADDR_GAME_STATE)

    def get_player_pos(self):
        """Returns (x, y) coordinates of the player."""
        x_raw = self.read_int(ADDR_PLAYER_X)
        y_raw = self.read_int(ADDR_PLAYER_Y)
        if x_raw is None or y_raw is None: return 0, 0
        return x_raw, y_raw

    def get_bullets(self):
        """Reads bullet data from the entity array and returns a list of Bullet objects."""
        count = self.read_int(ADDR_BULLET_COUNT)
        if count is None: return []
        if count > 300: count = 300 # Safety cap
        
        bullets = []
        for i in range(count):
            addr = ADDR_ENTITY_ARRAY + (i * ENTITY_SIZE)
            # Entity structure (15 bytes):
            # 0-3: X (int)
            # 4-7: Y (int)
            # 8  : Slot status (0xFF = End/Free)
            # 9  : active flag
            # 10 : type (1: Homing, 2: Bounce, 3: Adv)
            # 11 : timer
            # 12 : index
            # 13 : vx (int8)
            # 14 : vy (int8)
            data = self.read_memory(addr, 15)
            if not data: continue
            
            # Extract raw values
            # < = little-endian
            # I = uint32 (raw_x)
            # I = uint32 (raw_y)
            # B = uint8 (status, active, type, timer, index)
            # b = int8 (vx, vy)
            raw_vals = struct.unpack("<IIBBBBBbb", data)
            
            # Check slot status (Offset 8)
            if raw_vals[2] == 0xFF:
                continue
                
            bullets.append(Bullet(*raw_vals))
        return bullets

    def send_key(self, vk_code, duration=0.05):
        """Sends a key press event to the game window."""
        if not self.hwnd: return
        ctypes.windll.user32.PostMessageW(self.hwnd, WM_KEYDOWN, vk_code, 0)
        if duration > 0:
            time.sleep(duration)
            ctypes.windll.user32.PostMessageW(self.hwnd, WM_KEYUP, vk_code, 0)

    def move_up(self): self.send_key(VK_UP)
    def move_down(self): self.send_key(VK_DOWN)
    def move_left(self): self.send_key(VK_LEFT)
    def move_right(self): self.send_key(VK_RIGHT)
    def press_enter(self): self.send_key(VK_RETURN)

    def go_to_game(self):
        """Navigates from Title screen to the game."""
        state = self.get_game_state()
        if state == 0: # Title
            print("At Title screen. Starting game...")
            self.press_enter()
        elif state in [5, 6]: # Game Over / Result
            print("At Game Over screen. Returning to title...")
            self.press_enter()
            time.sleep(0.5)
            self.press_enter()

    def monitor(self):
        """Example loop to monitor the game state and show some bullet positions."""
        print("Monitoring game. Press Ctrl+C to stop.")
        state_map = {0: "Title", 1: "Playing", 5: "Result", 6: "Ranking"}
        try:
            while True:
                state = self.get_game_state()
                x, y = self.get_player_pos()
                bullets = self.get_bullets()
                
                state_str = state_map.get(state, f"State {state}")
                
                # Format bullet string for the first 5 bullets
                bullet_info = ", ".join([str(b) for b in bullets[:5]])
                if not bullet_info:
                    bullet_info = "None"

                print(f"\rState: {state_str:<8} | Player: ({x:>3}, {y:>3}) | Bullets: {len(bullets):>3} | First 5: {bullet_info:<60}", end="")
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nMonitoring stopped.")

if __name__ == "__main__":
    ctrl = GameControl()
    if ctrl.launch_game():
        # Example: start the game if at title
        ctrl.go_to_game()
        # Monitor
        ctrl.monitor()
