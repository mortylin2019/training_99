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
        self.sim_frames = 60      # 1.0s lookahead
        self.safety_margin = 0    # Using exact hitbox rect instead of margin
        self.move_speed = 1       # VERIFIED from ASM: G_PlayerX = G_PlayerX + iVar3 (1px/f)
        
        self.last_latency = 0

    def perform_move(self):
        start_eval = time.time()
        px, py = self.game.get_player_pos()
        bullets = self.game.get_bullets()
        frames = self.game.read_int(0x00406d88) or 0
        multiplier = self.game.read_int(0x00406d8c) or 16
        total_ms = frames * multiplier
        
        active_bullets = [b for b in bullets if b.angle_index != 0xFF]
        
        # Candidate directions (8-way + STAY)
        # Note: In most games, diagonal movement is 1px each way, not normalized.
        directions = {
            "STAY": (0, 0),
            "L": (-1, 0), "R": (1, 0), "U": (0, -1), "D": (0, 1),
            "LU": (-1, -1), "LD": (-1, 1), "RU": (1, -1), "RD": (1, 1)
        }
        bits_map = {
            "STAY": 0, "L": 1, "U": 2, "D": 4, "R": 8,
            "LU": 1|2, "LD": 1|4, "RU": 8|2, "RD": 8|4
        }
        
        # Game hitbox (from Stage2_GameEntityLoop.c): 
        # Collision if: 2 <= (bx - px) <= 12 AND 0 <= (by - py) <= 9
        # Coordinate Delta check from Stage2_GameEntityLoop.c:
        # if ((dX - 2U < 11) && (dY < 10))
        # dX = BX - PX, dY = BY - PY
        # So hit if: 2 <= BX-PX < 13 AND 0 <= BY-PY < 10

        # Simplified bullet prediction for simulation
        # pre-calculate bullet states at specific frame steps to speed up
        bullet_predict = []
        for b in active_bullets:
            states = []
            bx, by = b.x, b.y
            # Basic speed for angle-based bullets
            # In Stage2_GameEntityLoop.c, lookup tables suggest speed is approx 2.5-3.0 px/frame
            speed = 2.5 
            rad = b.angle_index * (2 * math.pi / 256)
            cos_a = math.cos(rad)
            sin_a = math.sin(rad)
            
            for f in range(self.sim_frames + 1):
                if b.type == 2:
                    # Type 2 uses raw vx/vy which are not shifted
                    # stage2: *local_2c = *local_2c + vx; -> raw_x += vx
                    # so dx = vx/64.0 per frame
                    states.append((bx + (b.vx/64.0)*f, by + (b.vy/64.0)*f))
                else:
                    states.append((bx + speed*f*cos_a, by + speed*f*sin_a))
            bullet_predict.append(states)

        best_branch_move = "STAY"
        max_branch_score = -999999999
        best_final_survival = 0

        # Two-stage lookahead: 81 paths (9 choices for 30f, then 9 choices for 30f)
        mid_f = self.sim_frames // 2
        
        for name1, (v1x, v1y) in directions.items():
            # First leg simulation
            survive1 = 0
            danger1 = 0
            px1, py1 = px, py
            collision1 = False
            
            for f in range(1, mid_f + 1):
                px1 = px + (v1x * self.move_speed * f)
                py1 = py + (v1y * self.move_speed * f)
                
                if px1 < 4 or px1 > 316 or py1 < 4 or py1 > 396:
                    collision1 = True; break
                
                for b_states in bullet_predict:
                    bx, by = b_states[f]
                    dx, dy = bx - px1, by - py1
                    # Exact Rectangular Hitbox check
                    if (2.0 <= dx < 13.0) and (0.0 <= dy < 10.0):
                        collision1 = True; break
                    
                    # Proximity danger (distance to center of hitbox)
                    dist_sq = (dx - 7.5)**2 + (dy - 5.0)**2
                    danger1 += 1.0 / (dist_sq + 1)
                if collision1: break
                survive1 += 1
            
            if collision1:
                # Still score it so we can pick the "least bad" move if all die
                score1 = (survive1 * 1000) - danger1
                if score1 > max_branch_score:
                    max_branch_score = score1
                    best_branch_move = name1
                    best_final_survival = survive1
                continue

            # Second leg simulation (only if first leg survives)
            for name2, (v2x, v2y) in directions.items():
                survive2 = 0
                danger2 = 0
                px2, py2 = px1, py1
                collision2 = False
                
                for f in range(mid_f + 1, self.sim_frames + 1):
                    # Relative frame in second leg
                    rel_f = f - mid_f
                    px2 = px1 + (v2x * self.move_speed * rel_f)
                    py2 = py1 + (v2y * self.move_speed * rel_f)
                    
                    if px2 < 4 or px2 > 316 or py2 < 4 or py2 > 396:
                        collision2 = True; break
                    
                    for b_states in bullet_predict:
                        bx, by = b_states[f]
                        dx, dy = bx - px2, by - py2
                        if (2.0 <= dx < 13.0) and (0.0 <= dy < 10.0):
                            collision2 = True; break
                        
                        dist_sq = (dx - 7.5)**2 + (dy - 5.0)**2
                        danger2 += 1.0 / (dist_sq + 1)
                    if collision2: break
                    survive2 += 1
                
                # Scoring
                total_survive = survive1 + survive2
                total_danger = danger1 + danger2
                
                # Target center-bottom (160, 200)
                dist_penalty = math.sqrt((px2-160)**2 + (py2-200)**2) * 5
                
                # Survival time is the highest priority. 
                score = (total_survive * 1000000) - (total_danger * 50) - dist_penalty
                
                if score > max_branch_score:
                    max_branch_score = score
                    best_branch_move = name1
                    best_final_survival = total_survive

        # Execute
        self.game.write_int(0x00406d7c, bits_map[best_branch_move])
        self.last_latency = (time.time() - start_eval) * 1000
        
        # Display: Match the game's display format: Seconds.Milliseconds
        print(f"\r[Score:{total_ms/1000:>6.3f}s] [T:{frames:>5}] [LAT:{self.last_latency:>2.0f}ms] [B:{len(active_bullets):>3}] Move:{best_branch_move:<4} | Forecast:{best_final_survival:>2}f   ", end="")
