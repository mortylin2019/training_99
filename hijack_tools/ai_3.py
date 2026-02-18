import time
import math
try:
    from game_control import GameControl
except ImportError:
    from hijack_tools.game_control import GameControl

class PlayerAI:
    def __init__(self, game_instance=None):
        self.game = game_instance if game_instance else GameControl()
        
        # Hyperparameters for the "Oracle" Logic
        self.sim_frames = 60      # Increased lookahead to 1.0s (60 frames)
        self.safety_margin = 10   # Slightly tighter safety to allow gap-threading
        self.move_speed = 4       # Estimated px per logical tick
        
        # Performance
        self.last_time = time.time()
        self.frame_count = 0
        self.current_fps = 0
        self.last_latency = 0

    def start(self):
        if not self.game.launch_game(): return
        last_state = -1
        try:
            while True:
                state = self.game.get_game_state()
                if state != last_state:
                    self.game.write_int(0x00406d7c, 0)
                    if state in [0, 5, 6]: self.game.press_enter()
                    last_state = state

                if state == 1:
                    self.perform_move()
                    self.frame_count += 1
                    if time.time() - self.last_time >= 1.0:
                        self.current_fps = self.frame_count
                        self.frame_count = 0
                        self.last_time = time.time()
                    time.sleep(0.01)
                else:
                    self.game.write_int(0x00406d7c, 0)
                    time.sleep(0.1)
        except KeyboardInterrupt:
            self.game.write_int(0x00406d7c, 0)

    def perform_move(self):
        start_eval = time.time()
        px, py = self.game.get_player_pos()
        bullets = self.game.get_bullets()
        # Read survival frames (Score) from 0x00406d88
        # Read multiplier from 0x00406d8c (usually 16 for Normal, 12 for Hard)
        frames = self.game.read_int(0x00406d88) or 0
        multiplier = self.game.read_int(0x00406d8c) or 16
        total_ms = frames * multiplier
        
        active_bullets = [b for b in bullets if b.angle_index != 0xFF]

        if not active_bullets:
            self.game.write_int(0x00406d7c, 0)
            return

        # Possible velocity vectors for the player (8-way + STAY)
        candidates = {
            "STAY": (0, 0),
            "L": (-1, 0), "R": (1, 0), "U": (0, -1), "D": (0, 1),
            "LU": (-0.7, -0.7), "LD": (-0.7, 0.7), "RU": (0.7, -0.7), "RD": (0.7, 0.7)
        }
        
        bits_map = {
            "STAY": 0, "L": 1, "U": 2, "D": 4, "R": 8,
            "LU": 1|2, "LD": 1|4, "RU": 8|2, "RD": 8|4
        }

        best_move = "STAY"
        max_score = -9999999
        final_survival = 0

        for name, (v_x, v_y) in candidates.items():
            survival_frames = 0
            collision_occurred = False
            total_path_danger = 0
            
            # Predict collisions over sim_frames
            for f in range(1, self.sim_frames + 1):
                ppx = px + (v_x * self.move_speed * f)
                ppy = py + (v_y * self.move_speed * f)
                
                # Boundary check - if we hit a wall, that's the end of survival for this path
                if ppx < 8 or ppx > 312 or ppy < 8 or ppy > 232:
                    collision_occurred = True
                    break
                
                frame_danger = 0
                for b in active_bullets:
                    bx, by = b.x, b.y
                    if b.type == 2:
                        bx += b.vx * f
                        by += b.vy * f
                    else:
                        bx += (f * 2.5) * math.cos(b.angle_index * 2 * math.pi / 256)
                        by += (f * 2.5) * math.sin(b.angle_index * 2 * math.pi / 256)
                    
                    dist_sq = (ppx - bx)**2 + (ppy - by)**2
                    if dist_sq < self.safety_margin**2:
                        collision_occurred = True
                        break
                    
                    # Inverse distance law for path danger
                    frame_danger += 100.0 / (dist_sq + 1)
                
                if collision_occurred: break
                survival_frames += 1
                total_path_danger += frame_danger

            # Scoring: Primary is survival time, secondary is low path danger, tertiary is center bias
            center_dist = math.sqrt((px - 160)**2 + (py - 180)**2)
            # Factor in movement penalty to reduce jitter
            move_penalty = 50 if name != "STAY" else 0
            
            score = (survival_frames * 5000) - total_path_danger - (center_dist * 2) - move_penalty

            if score > max_score:
                max_score = score
                best_move = name
                final_survival = survival_frames

        # Inject move
        self.game.write_int(0x00406d7c, bits_map[best_move])
        self.last_latency = (time.time() - start_eval) * 1000
        
        # Display: Game Score | Raw Tick | Process Latency | Survival Forecast
        # Match the game's display format: Seconds.Milliseconds
        print(f"\r[Score:{total_ms/1000:>6.3f}s] [T:{frames:>5}] [LAT:{self.last_latency:>2.0f}ms] [B:{len(active_bullets):>3}] Move:{best_move:<4} | Forecast:{final_survival:>2}f   ", end="")
