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
                    time.sleep(0.01) # High frequency in play
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
        
        # Directions to test: (dx, dy)
        directions = {
            "STAY": (0, 0),
            "UP": (0, -self.step),
            "DOWN": (0, self.step),
            "LEFT": (-self.step, 0),
            "RIGHT": (self.step, 0)
        }
        
        best_dir = "STAY"
        min_score = 999999.0
        
        # Use .active flag for better reliability
        active_bullets = [b for b in bullets if b.active == 1]
        
        for name, (dx, dy) in directions.items():
            tx, ty = px + dx, py + dy
            
            # Boundary check
            if tx < 10 or tx > 300 or ty < 10 or ty > 220:
                continue
                
            threat = 0
            for b in active_bullets:
                bx, by = b.x, b.y
                # Prediction for bouncing bullets
                if b.type == 2:
                    bx += b.vx * 15
                    by += b.vy * 15
                
                dist_sq = (tx - bx)**2 + (ty - by)**2
                # Buffer of ~20 pixels
                if dist_sq < 400:
                    threat += 100
            
            # Weighted choice: stay near center-bottom and avoid unnecessary movement
            center_dist = math.sqrt((tx - 152)**2 + (ty - 180)**2)
            bias = center_dist / 20.0 # Weaker pull
            move_penalty = 8.0 if name != "STAY" else 0.0 # Stronger penalty for moving
            
            score = threat + bias + move_penalty
            
            if score < min_score:
                min_score = score
                best_dir = name
        
        # Directly inject movement into G_InputState (0x00406d7c)
        input_map = {"STAY": 0, "LEFT": 1, "DOWN": 2, "UP": 4, "RIGHT": 8}
        input_bits = input_map.get(best_dir, 0)
        self.game.write_int(0x00406d7c, input_bits)
        
        print(f"\r[PI:{len(active_bullets):>3}] Pos:({px:>3},{py:>3}) | Move:{best_dir:<5} | Score:{int(min_score)}   ", end="")

if __name__ == "__main__":
    ai = PlayerAI()
    ai.start()
