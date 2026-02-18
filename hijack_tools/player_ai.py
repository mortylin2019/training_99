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
        
        # Directions: (dx, dy)
        directions = {
            "STAY": (0, 0),
            "UP": (0, -self.step),
            "DOWN": (0, self.step),
            "LEFT": (-self.step, 0),
            "RIGHT": (self.step, 0)
        }
        
        best_dir = "STAY"
        min_score = float('inf')
        
        # Filter active bullets. Based on RE, angle_index != 0xFF is the primary indicator.
        # We'll use active > 0 as a secondary check if available.
        active_bullets = [b for b in bullets if b.angle_index != 0xFF]
        
        for name, (dx, dy) in directions.items():
            tx, ty = px + dx, py + dy
            
            # Boundary check
            if tx < 5 or tx > 310 or ty < 5 or ty > 230:
                continue
                
            threat_score = 0
            for b in active_bullets:
                bx, by = b.x, b.y
                
                # Simple linear prediction for bouncing bullets
                if b.type == 2:
                    bx += b.vx * 10
                    by += b.vy * 10
                
                dist = math.sqrt((tx - bx)**2 + (ty - by)**2)
                
                # COLLISION ZONE (Danger!)
                if dist < 15:
                    threat_score += 5000 / (dist + 1) # Exponentially bad
                # CAUTION ZONE
                elif dist < self.safety_radius:
                    threat_score += (self.safety_radius - dist) * 10
            
            # Weighted bias: prefer center-bottom (152, 200)
            target_x, target_y = 152, 200
            center_dist = math.sqrt((tx - target_x)**2 + (ty - target_y)**2)
            
            bias = center_dist / 10.0
            move_penalty = 15.0 if name != "STAY" else 0.0
            
            total_score = threat_score + bias + move_penalty
            
            if total_score < min_score:
                min_score = total_score
                best_dir = name
        
        # Inject move
        input_map = {"STAY": 0, "LEFT": 1, "DOWN": 2, "UP": 4, "RIGHT": 8}
        self.game.write_int(0x00406d7c, input_map.get(best_dir, 0))
        
        # Debug output
        print(f"\r[FPS:{self.current_fps:>2.0f}] [Bullets:{len(active_bullets):>3}] Pos:({px:>3},{py:>3}) | Move:{best_dir:<5} | Score:{int(min_score):>4}   ", end="")

if __name__ == "__main__":
    ai = PlayerAI()
    ai.start()
