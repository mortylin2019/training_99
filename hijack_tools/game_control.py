import ctypes
import time
import subprocess
import os
import struct
try:
    from bullet_data import Bullet
except ImportError:
    from hijack_tools.bullet_data import Bullet

# Windows Constants
PROCESS_ALL_ACCESS = 0x1F0FFF
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
ADDR_GAME_STATE = 0x00406d74 # Real game state machine
ADDR_PAUSE_FLAG = 0x00406d84 # 1 = Active/Playing, 0 = Paused/Menu
ADDR_INPUT_STATE = 0x00406d7c
ADDR_GAME_OVER = 0x00406d80 # 1 if dead, 0 if alive
ADDR_GAME_TIME = 0x00406d88 # Raw frames/ticks
ADDR_SCORE_MULTIPLIER = 0x00406d8c
ADDR_BULLET_COUNT = 0x00406da8
ADDR_ENTITY_ARRAY = 0x00406e10
ENTITY_SIZE = 15 # The game increments entity pointer by 0x0F (15 bytes)

class GameControl:
    def __init__(self, exe_path=r"C:\git\training_99\raw\99.exe"):
        self.exe_path = exe_path
        self.process_handle = None
        self.pid = None
        self.hwnd = None
        self.proc = None

    def launch_game(self):
        """Launches the game and attaches to its process."""
        print(f"Launching {self.exe_path}...")
        try:
            self.proc = subprocess.Popen(self.exe_path, cwd=os.path.dirname(self.exe_path))
            self.pid = self.proc.pid
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

    def write_memory(self, address, data):
        """Writes data to the process memory."""
        if not self.process_handle: return False
        bytes_written = ctypes.c_size_t()
        return ctypes.windll.kernel32.WriteProcessMemory(
            self.process_handle, address, data, len(data), ctypes.byref(bytes_written)
        )

    def write_int(self, address, value):
        """Writes a 4-byte integer to the process memory."""
        data = struct.pack("<I", value)
        return self.write_memory(address, data)

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

    def send_key(self, vk_code, duration=0.03):
        """Sends a key press event to the game window."""
        if not self.hwnd: return
        # Using SendMessage for more reliable input than PostMessage
        # WM_KEYDOWN = 0x100, WM_KEYUP = 0x101
        ctypes.windll.user32.SendMessageW(self.hwnd, 0x100, vk_code, 0)
        if duration > 0:
            time.sleep(duration)
            ctypes.windll.user32.SendMessageW(self.hwnd, 0x101, vk_code, 0)

    def move_up(self): self.send_key(VK_UP, duration=0.03)
    def move_down(self): self.send_key(VK_DOWN, duration=0.03)
    def move_left(self): self.send_key(VK_LEFT, duration=0.03)
    def move_right(self): self.send_key(VK_RIGHT, duration=0.03)
    def press_enter(self): self.send_key(VK_RETURN, duration=0.1)

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

    def cleanup(self):
        """Kills the game process if it is running."""
        if self.proc:
            print(f"\nClosing game process (PID: {self.pid})...")
            self.proc.terminate()
            try:
                self.proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.proc.kill()

    def run_ai(self):
        """Runs the AI avoidance logic with state management and logging."""
        # ai_3: Oracle Simulation (Predictive Logic) - RECOMMENDED
        from ai_3 import PlayerAI
        ai = PlayerAI(self)
        
        if not self.launch_game(): return
        
        in_run = False
        max_bullets = 0
        
        print("AI Controller started. Monitoring game states...")
        
        try:
            while True:
                # 0x406d84 (PauseFlag) is the most reliable "In Active Play" indicator.
                # It is 1 when unpaused and playing, 0 in menus/pause.
                is_playing = self.read_int(ADDR_PAUSE_FLAG) == 1
                is_dead = self.read_int(ADDR_GAME_OVER) == 1
                state = self.read_int(ADDR_GAME_STATE)
                
                # Check for run start
                if is_playing and not is_dead and not in_run:
                    in_run = True
                    max_bullets = 0
                    print(f"\n[NEW GAME] Started at {time.strftime('%H:%M:%S')}")

                # Check for run end
                if in_run and (not is_playing or is_dead):
                    in_run = False
                    frames = self.read_int(ADDR_GAME_TIME) or 0
                    multiplier = self.read_int(ADDR_SCORE_MULTIPLIER) or 16
                    final_sec = (frames * multiplier) / 1000
                    print(f"\n[RUN FINISHED] Time: {final_sec:.3f}s | Ticks: {frames} | Max Bullets: {max_bullets}")
                    time.sleep(1.0) 

                # Auto-navigation for menus (State machine based)
                # If we are not playing and not dead, we are likely in a menu
                if not is_playing and not in_run:
                    self.write_int(ADDR_INPUT_STATE, 0)
                    self.press_enter()
                    time.sleep(0.2)

                # Active Gameplay Logic
                if in_run and is_playing:
                    bullets = self.get_bullets()
                    active_count = len([b for b in bullets if b.angle_index != 0xFF])
                    if active_count > max_bullets:
                        max_bullets = active_count
                        
                    ai.perform_move()
                    time.sleep(0.01)
                else:
                    time.sleep(0.1)
                    
        except KeyboardInterrupt:
            self.write_int(ADDR_INPUT_STATE, 0)
            print("\nAI Controller stopped by user.")
        finally:
            self.cleanup()

if __name__ == "__main__":
    game = GameControl()
    game.run_ai()
