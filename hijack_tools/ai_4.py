import time
import math
import heapq
try:
    from game_control import GameControl
except ImportError:
    from hijack_tools.game_control import GameControl

class TimeSpaceAStar:
    """
    Advanced Time-Space A* Pathfinding.
    1 Step = 4 Frames (4px movement)
    Grid: 4x4 px cells
    """
    def __init__(self, game_instance=None):
        self.game = game_instance if game_instance else GameControl()
        
        # Hyperparameters
        self.step_frames = 4        # 1 step = 4 frames
        self.max_steps = 15         # 15 * 4 = 60 frames lookahead
        self.grid_size = 4          # 4x4 px grid
        
        # Grid dimensions (320x400)
        self.cols = 320 // self.grid_size
        self.rows = 400 // self.grid_size

    def get_grid_pos(self, px, py):
        return int(px // self.grid_size), int(py // self.grid_size)

    def get_world_pos(self, gx, gy):
        return gx * self.grid_size, gy * self.grid_size

    def check_collision(self, px, py, frame, bullet_predict):
        # Boundaries
        if px < 4 or px > 316 or py < 4 or py > 396:
            return True
        
        # Check every frame in the step for safety
        start_f = max(0, frame - self.step_frames + 1)
        for f in range(start_f, frame + 1):
            if f >= len(bullet_predict[0]): break
            for b_states in bullet_predict:
                bx, by = b_states[f]
                dx, dy = bx - px, by - py
                if (2.0 <= dx < 13.0) and (0.0 <= dy < 10.0):
                    return True
        return False

    def get_danger_score(self, px, py, frame, bullet_predict):
        danger = 0
        for b_states in bullet_predict:
            bx, by = b_states[frame]
            # Distance squared to bullet center
            dist_sq = (bx - (px + 7.5))**2 + (by - (py + 5.0))**2
            if dist_sq < 3600: # 60px radius
                danger += 5000.0 / (dist_sq + 10)
        
        # Wall avoidance: strong penalty for being near edges
        if px < 40 or px > 280: danger += 1000
        if py < 40 or py > 360: danger += 1000
        return danger

    def perform_move(self):
        start_time = time.time()
        px, py = self.game.get_player_pos()
        bullets = self.game.get_bullets()
        active_bullets = [b for b in bullets if b.angle_index != 0xFF]
        
        if not active_bullets:
            self.game.write_int(0x00406d7c, 0)
            return

        total_frames = self.max_steps * self.step_frames
        
        # 1. OPTIMIZATION: Index bullets by frame (Flat structure)
        bullets_by_frame = [[] for _ in range(total_frames + 1)]
        for b in active_bullets:
            bx, by = b.raw_x / 64.0, b.raw_y / 64.0
            vx, vy = b.vx / 64.0, b.vy / 64.0
            
            # Prediction Loop
            cbx, cby = bx, by
            cvx, cvy = vx, vy
            
            for f in range(total_frames + 1):
                bullets_by_frame[f].append((cbx, cby))
                
                # If Homing (Type 1), simulate steering toward current player
                if b.type == 1:
                    # Steering Logic simplified from Entity_Type1_Homing.c:
                    # Target is player pos. Vector = Target - Bullet.
                    # This is an approximation as we don't know the exact future player pos 
                    # for every path, so we use current px/py as the lure.
                    dx, dy = px - cbx, py - cby
                    dist = math.sqrt(dx*dx + dy*dy) + 0.1
                    # Steer vector (normalized) * small factor
                    cvx += (dx / dist) * 0.2
                    cvy += (dy / dist) * 0.2
                    # Velocity cap (approx 2.5px/f)
                    mag = math.sqrt(cvx*cvx + cvy*cvy)
                    if mag > 2.5:
                        cvx = (cvx / mag) * 2.5
                        cvy = (cvy / mag) * 2.5
                
                cbx += cvx
                cby += cvy

        # 2. A* Search
        start_gx, start_gy = self.get_grid_pos(px, py)
        queue = []
        heapq.heappush(queue, (0, 0, start_gx, start_gy, 0))
        
        visited = {} 
        best_state = (0, start_gx, start_gy, 0)
        
        moves = [
            (0, 0, 0), ( -1, 0, 1), (0, -1, 2), (0, 1, 4), (1, 0, 8),
            (-1, -1, 3), (-1, 1, 5), (1, -1, 10), (1, 1, 12)
        ]

        max_iter = 400 
        iters = 0
        
        while queue and iters < max_iter:
            iters += 1
            pri, s, gx, gy, first_bits = heapq.heappop(queue)
            
            if s > best_state[0]:
                best_state = (s, gx, gy, first_bits)
            elif s == best_state[0] and pri < visited.get((best_state[1], best_state[2], s), 999999):
                best_state = (s, gx, gy, first_bits)

            if s >= self.max_steps: continue
            
            next_s = s + 1
            next_f = next_s * self.step_frames
            n_bullets = bullets_by_frame[next_f]
            
            for dx, dy, bits in moves:
                ngx, ngy = gx + dx, gy + dy
                if 2 <= ngx < self.cols - 2 and 2 <= ngy < self.rows - 2:
                    state_key = (ngx, ngy, next_s)
                    npx, npy = ngx * self.grid_size, ngy * self.grid_size
                    
                    # Optimized Collision with 2x Safety Buffer
                    collision = False
                    # Check midway and end frame of the step to prevent "tunneling"
                    mid_f = next_f - 2
                    for f_idx in [mid_f, next_f]:
                        curr_bullets = bullets_by_frame[f_idx]
                        # Move player partway for mid_f check
                        check_px = npx if f_idx == next_f else (gx + dx*0.5)*self.grid_size
                        check_py = npy if f_idx == next_f else (gy + dy*0.5)*self.grid_size
                        
                        for bx, by in curr_bullets:
                            # Broad-phase check
                            if abs(bx - check_px) < 22 and abs(by - check_py) < 20:
                                dx_rel, dy_rel = bx - check_px, by - check_py
                                # 2x Expanded Hitbox for Safety Buffer
                                # Original: 2 <= dx < 13 (w=11) and 0 <= dy < 10 (h=10)
                                # Centered expansion (2x): X: [-3.5, 18.5], Y: [-5.0, 15.0]
                                if (-3.5 <= dx_rel < 18.5) and (-5.0 <= dy_rel < 15.0):
                                    collision = True; break
                        if collision: break
                    
                    if not collision:
                        # Danger Score (Manhattan-based is faster)
                        danger = 0
                        for bx, by in n_bullets:
                            d_dist = abs(bx - (npx+7.5)) + abs(by - (npy+5.0))
                            if d_dist < 50:
                                danger += 5000 / (d_dist + 1)
                        
                        # Penalize corners/walls (Increase penalty)
                        if npx < 80 or npx > 240: danger += 2000
                        if npy < 80 or npy > 320: danger += 2000

                        dist_to_goal = abs(npx - 160) + abs(npy - 280) * 1.5
                        new_pri = -next_s * 5000 + dist_to_goal + danger
                        
                        if state_key not in visited or new_pri < visited[state_key]:
                            visited[state_key] = new_pri
                            f_bits = first_bits if s > 0 else bits
                            heapq.heappush(queue, (new_pri, next_s, ngx, ngy, f_bits))

        # 3. Execute
        exec_bits = best_state[3]
        self.game.write_int(0x00406d7c, exec_bits)
        
        latency = (time.time() - start_time) * 1000
        print(f"\r[A* Path] Depth:{best_state[0]:>2} steps | Iters:{iters:>4} | Latency:{latency:>2.0f}ms | Move:{exec_bits:<2}      ", end="")

        # 3. Execute
        exec_bits = best_state[3]
        self.game.write_int(0x00406d7c, exec_bits)
        
        latency = (time.time() - start_time) * 1000
        print(f"\r[A* Path] Depth:{best_state[0]:>2} steps | Iters:{iters:>4} | Latency:{latency:>2.0f}ms | Move:{exec_bits:<2}      ", end="")

if __name__ == "__main__":
    ai = TimeSpaceAStar()
    # Manual test loop if needed
