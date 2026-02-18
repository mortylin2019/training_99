import time
import math
try:
    from game_control import GameControl
except ImportError:
    from hijack_tools.game_control import GameControl

class PlayerAI:
    def __init__(self):
        self.game = GameControl()
        self.radius = 10
        self.step = 10
        self.safety_radius = 25 # Increased from 20
        self.threat_gain = 100
        self.fps_limit = 0.01 # Target ~100 FPS
        self.last_time = time.time()
        self.frame_count = 0
        self.current_fps = 0
        
    def start(self):
        if not self.game.launch_game():
            print("Failed to launch game.")
            return
            
        print("AI Active. Monitoring game state...")
        last_state = -1
        try:
            while True:
                state = self.game.get_game_state()
                
                # Log state changes only
                if state != last_state:
                    state_map = {0: "TITLE", 1: "PLAYING", 5: "RESULT", 6: "RANKING"}
                    print(f"\n[AI] State: {state_map.get(state, f'ID {state}')}")
                    
                    # Reset input on state change to prevent stuck movement
                    self.game.write_int(0x00406d7c, 0)
                    
                    # Auto start if we enter Title or Result/Ranking
                    if state in [0, 5, 6]:
                        print("[AI] Auto-navigating...")
                        self.game.press_enter()
                    
                    last_state = state

                if state == 1: # Playing
                    self.perform_move()
                    
                    # FPS Calculation
                    self.frame_count += 1
                    now = time.time()
                    elapsed = now - self.last_time
                    if elapsed >= 1.0:
                        self.current_fps = self.frame_count / elapsed
                        self.frame_count = 0
                        self.last_time = now
                        
                    time.sleep(self.fps_limit)
                else:
                    # Clear input buffer when not playing
                    self.game.write_int(0x00406d7c, 0)
                    time.sleep(0.1) # Low frequency in menus
        except KeyboardInterrupt:
            self.game.write_int(0x00406d7c, 0) # Safety stop
            print("\nAI Stopped.")

    def perform_move(self):
        px, py = self.game.get_player_pos()
        bullets = self.game.get_bullets()
        active_bullets = [b for b in bullets if b.angle_index != 0xFF]
        
        if not active_bullets:
            # If no bullets, don't move
            self.game.write_int(0x00406d7c, 0)
            print(f"\r[FPS:{self.current_fps:>2.0f}] [B:  0] Pos:({px:>3},{py:>3}) | Move:STAY  | Status:CLEAR   ", end="")
            return

        # Vector-based Repulsion: sum of normalized vectors away from every bullet
        rx, ry = 0.0, 0.0
        for b in active_bullets:
            dx = px - b.x
            dy = py - b.y
            dist_sq = dx*dx + dy*dy
            if dist_sq < 1: dist_sq = 1
            dist = math.sqrt(dist_sq)
            
            # Repulsion weight increases sharply as distance decreases
            weight = 1000.0 / dist_sq
            rx += (dx / dist) * weight
            ry += (dy / dist) * weight

        # Tactical Home: Pull towards screen center (160, 120)
        cx, cy = 160 - px, 120 - py
        c_dist = math.sqrt(cx*cx + cy*cy) or 1.0
        
        # Home pull is now significantly stronger when pressure is low
        # Scales with distance but has a higher baseline
        home_pull = 0.8
        rx += (cx / c_dist) * home_pull
        ry += (cy / c_dist) * home_pull

        # Boundary Repulsion: Push away from edges (50px margin)
        margin = 50
        if px < margin: rx += (margin - px) / 10.0
        if px > (320 - margin): rx -= (px - (320 - margin)) / 10.0
        if py < margin: ry += (margin - py) / 10.0
        if py > (240 - margin): ry -= (py - (240 - margin)) / 10.0

        # Movement Resolution (Supports Diagonals)
        input_bits = 0
        
        # Horizontal
        if rx > 0.1:  input_bits |= 8  # RIGHT
        elif rx < -0.1: input_bits |= 1  # LEFT
        
        # Vertical
        if ry > 0.1:  input_bits |= 4  # DOWN
        elif ry < -0.1: input_bits |= 2  # UP

        # Boundary Safety: Mask bits if moving into walls
        if px < 15: input_bits &= ~1 # Block LEFT
        if px > 305: input_bits &= ~8 # Block RIGHT
        if py < 15: input_bits &= ~2 # Block UP
        if py > 225: input_bits &= ~4 # Block DOWN

        # Inject move
        self.game.write_int(0x00406d7c, input_bits)
        
        # Debug Output
        move_desc = []
        if input_bits & 1: move_desc.append("L")
        if input_bits & 8: move_desc.append("R")
        if input_bits & 2: move_desc.append("U")
        if input_bits & 4: move_desc.append("D")
        move_str = "".join(move_desc) if move_desc else "STAY"
        
        print(f"\r[FPS:{self.current_fps:>2.0f}] [B:{len(active_bullets):>3}] Pos:({px:>3},{py:>3}) | Move:{move_str:<5} | Pressure:{math.sqrt(rx*rx+ry*ry):>7.4f}   ", end="")

if __name__ == "__main__":
    ai = PlayerAI()
    ai.start()
