import time
import math
try:
    from game_control import GameControl
except ImportError:
    from hijack_tools.game_control import GameControl

class PlayerAI:
    def __init__(self, game_instance=None):
        self.game = game_instance if game_instance else GameControl()
        self.grid_size = 5 # Reduced from 10
        self.cols = 320 // self.grid_size
        self.rows = 240 // self.grid_size
        
        # Performance
        self.last_time = time.time()
        self.frame_count = 0
        self.current_fps = 0

    def start(self):
        if not self.game.launch_game():
            return
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
        px, py = self.game.get_player_pos()
        bullets = self.game.get_bullets()
        active_bullets = [b for b in bullets if b.angle_index != 0xFF]

        if not active_bullets:
            self.game.write_int(0x00406d7c, 0)
            return

        # 1. Prediction of bullet positions
        predict_pos = []
        for b in active_bullets:
            bx, by = b.x, b.y
            if b.type == 2:
                bx += b.vx * 5
                by += b.vy * 5
            predict_pos.append((bx, by))

        # 2. Evaluate all 9 cardinal directions (including STAY)
        # We pick the direction that minimizes the sum of 1/dist^2
        moves = {
            "STAY": (0, 0),
            "L": (-10, 0), "R": (10, 0), "U": (0, -10), "D": (0, 10),
            "LU": (-10, -10), "LD": (-10, 10), "RU": (10, -10), "RD": (10, 10)
        }
        
        bits_map = {
            "STAY": 0, "L": 1, "U": 2, "D": 4, "R": 8,
            "LU": 1|2, "LD": 1|4, "RU": 8|2, "RD": 8|4
        }

        best_move = "STAY"
        min_danger = float('inf')

        for name, (dx, dy) in moves.items():
            tx, ty = px + dx, py + dy
            
            # Simple Boundary check: don't evaluate moves that go off-screen
            if tx < 5 or tx > 315 or ty < 5 or ty > 235:
                continue

            total_danger = 0.0
            for bx, by in predict_pos:
                d2 = (tx - bx)**2 + (ty - by)**2
                if d2 < 1: d2 = 1
                total_danger += 1.0 / d2
            
            # Weighted Scoring: Total Danger + Center Pull
            # We use a significant divisor for center_dist so it acts as 
            # "gravity" when no immediate bullets are nearby.
            center_pull = math.sqrt((tx-160)**2 + (ty-120)**2) / 2000.0
            stay_bonus = -0.00001 if name == "STAY" else 0
            
            score = total_danger + center_pull + stay_bonus
            
            if score < min_danger:
                min_danger = score
                best_move = name

        # 3. Inject move
        self.game.write_int(0x00406d7c, bits_map[best_move])
            
        print(f"\r[FPS:{self.current_fps:>2}] [B:{len(active_bullets):>3}] Pos:({px:>3},{py:>3}) | Move:{best_move:<4} | Danger:{min_danger:>7.4f}   ", end="")
