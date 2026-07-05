"""
multi_runner.py — Run N AI-controlled game instances in parallel.

Launches N copies of 99.exe, tiles windows on screen, each with its own AI.
Gameplay uses G_InputState writes. Menu keys use SetForegroundWindow + keybd_event.

Usage:
    python hijack_tools/multi_runner.py -n 5 --ai ai_beam
    python hijack_tools/multi_runner.py -n 10 --runs 2
"""

import time
import sys
import ctypes
import json
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from loguru import logger

try:
    from game_control import GameControl
except ImportError:
    from hijack_tools.game_control import GameControl

logger.remove()
# Console: INFO+ only — clean, focused output
logger.add(sys.stderr, level="INFO", format="<level>{message}</level>")
# File: DEBUG+ — full details for post-mortem analysis
logger.add("logs/multi_runner_debug.log", level="DEBUG", rotation="10 MB",
           format="{time:HH:mm:ss.SSS} | {level:7} | {message}")


def tile_window(hwnd, col, row, cols, rows):
    """Pack windows in a tight grid — 320×240 each, 4px gap."""
    gap = 4
    w = 320
    h = 240
    x = col * (w + gap)
    y = row * (h + gap)
    # Move without resize, no z-order change, no activate
    ctypes.windll.user32.SetWindowPos(hwnd, 0, x, y, 0, 0, 0x0001 | 0x0004 | 0x0010)


def load_ai(name):
    if name == "ai_beam":
        from ai_beam import BeamAI
        return BeamAI
    if name == "ai_direct":
        from ai_direct import SuperiorAI
        return SuperiorAI
    raise ValueError(f"Unknown AI: {name}")


def send_enter(hwnd):
    """Send VK_RETURN to a specific window via PostMessage."""
    ctypes.windll.user32.PostMessageW(hwnd, 0x100, 0x0D, 0)
    time.sleep(0.05)
    ctypes.windll.user32.PostMessageW(hwnd, 0x101, 0x0D, 0)


def _warmup_ai(ai):
    """Force JIT compilation before gameplay starts."""
    from bullet_data import Bullet
    fake = [Bullet(raw_x=0x8000, raw_y=0x4000, angle_index=10, grazed=0,
                   type=0, timer=0, counter=0, vx=0, vy=0) for _ in range(20)]
    for _ in range(3):
        ai.decide(152, 44, fake)
    logger.debug("AI warmup complete")


def analyze_death(px, py, bullets):
    """Analyze what killed the player. Returns a debug string."""
    active = [b for b in bullets if b.angle_index != 0xFF]
    if not active:
        return "no bullets"

    # Find bullets that would hit the player hitbox
    killers = []
    nearby = []
    for b in active:
        dx = b.x - px
        dy = b.y - py
        if 2 <= dx < 13 and 0 <= dy < 10:
            killers.append(b)
        dist = (dx*dx + dy*dy) ** 0.5
        if dist < 50:
            nearby.append((dist, b))

    # Player screen position analysis
    edge = ""
    if px < 30: edge = "LEFT-EDGE"
    elif px > 274: edge = "RIGHT-EDGE"
    if py < 30: edge += " TOP-EDGE"
    elif py > 194: edge += " BOTTOM-EDGE"
    if not edge: edge = "open"

    # Bullet types near player
    type_counts = {}
    for _, b in nearby:
        type_names = {0: "Normal", 1: "Homing", 2: "H-Accel", 3: "Accel"}
        name = type_names.get(b.type, f"T{b.type}")
        type_counts[name] = type_counts.get(name, 0) + 1

    nearby_str = " ".join(f"{c}×{t}" for t, c in sorted(type_counts.items()))
    killer_str = ""
    if killers:
        k = killers[0]
        killer_str = f"killer: T{k.type} at ({k.x:.0f},{k.y:.0f}) dist={((k.x-px)**2+(k.y-py)**2)**0.5:.0f}"

    return f"pos=({px},{py}) {edge} | {len(nearby)} near: {nearby_str} | {killer_str}"


def run_instance(instance_id, ai_name, runs_per_instance, col, row, cols, rows):
    """
    Run one game instance with its own AI. Returns list of run records.
    """
    game = GameControl()
    if not game.launch_game():
        logger.error(f"[I{instance_id}] Launch FAILED")
        return []
    logger.info(f"[I{instance_id}] PID={game.pid} HWND=0x{game.hwnd:X}")

    if game.hwnd:
        tile_window(game.hwnd, col, row, cols, rows)

    AI = load_ai(ai_name)
    ai = AI(vel_table=game.vel_table, accel_table=game.accel_table)

    # Warm up JIT compilation BEFORE the game starts
    _warmup_ai(ai)

    history = []
    in_run = False
    max_bullets = 0
    run_count = 0
    types_seen = {}
    patterns_seen = {}
    graze_max = 0
    last_pattern = -1
    last_bullets = []   # for death analysis
    last_px = last_py = 0

    try:
        while run_count < runs_per_instance:
            # Keep game alive: clear tab-out flag, set IsGameRunning
            game.write_int(0x00406d9c, 0)  # DAT_00406d9c = not tabbed out
            game.write_int(0x00406d90, 1)  # G_IsGameRunning = 1

            is_playing = game.is_playing()
            is_dead = game.is_game_over()

            # Run start
            if is_playing and not is_dead and not in_run:
                in_run = True
                max_bullets = 0
                types_seen = {}
                patterns_seen = {}
                graze_max = 0
                last_pattern = -1
                run_count += 1

            # Run end
            if in_run and (not is_playing or is_dead):
                in_run = False
                ms = game.get_survival_ms()
                frames = game.get_game_time()
                mult = game.get_score_multiplier() or 1
                death_info = analyze_death(last_px, last_py, last_bullets)
                history.append({
                    "instance": instance_id,
                    "run": run_count,
                    "survival_ms": ms,
                    "survival_s": ms / 1000.0,
                    "frames": frames,
                    "multiplier": mult,
                    "max_bullets": max_bullets,
                    "graze_max": graze_max,
                    "types": dict(types_seen),
                    "patterns": dict(patterns_seen),
                    "death": death_info,
                })
                pstr = ",".join(f"P{p}={c}" for p, c in sorted(patterns_seen.items()))
                tstr = ",".join(f"T{t}≤{c}" for t, c in sorted(types_seen.items()))
                logger.success(
                    f"[I{instance_id}] Run {run_count}: {ms}ms ({ms/1000:.1f}s) "
                    f"| B:{max_bullets} Grz:{graze_max} | [{tstr}] | [{pstr}]"
                )
                logger.debug(f"[I{instance_id}] Death: {death_info}")
                game.write_int(0x00406d7c, 0)
                time.sleep(0.3)

            # Menu navigation — per-window PostMessage, no focus needed
            if not is_playing and not in_run:
                game.write_int(0x00406d7c, 0)
                send_enter(game.hwnd)
                time.sleep(0.2)
                continue

            # Gameplay
            if in_run and is_playing:
                px, py = game.get_player_pos()
                bullets = game.get_bullets()
                active = [b for b in bullets if b.angle_index != 0xFF]

                # Save for death analysis
                last_px, last_py = px, py
                last_bullets = bullets

                if len(active) > max_bullets:
                    max_bullets = len(active)

                # Track bullet type peaks (max seen at any one frame)
                frame_types = {}
                for b in active:
                    frame_types[b.type] = frame_types.get(b.type, 0) + 1
                for t, c in frame_types.items():
                    if c > types_seen.get(t, 0):
                        types_seen[t] = c

                # Track patterns
                pat = game.get_next_pattern()
                if pat != last_pattern:
                    patterns_seen[pat] = patterns_seen.get(pat, 0) + 1
                    last_pattern = pat

                # Track graze
                grz = game.get_active_near()
                if grz > graze_max:
                    graze_max = grz

                bits = ai.decide(px, py, active)
                game.write_int(0x00406d7c, bits)

    except Exception as e:
        logger.error(f"[Instance {instance_id}] Error: {e}")
    finally:
        game.write_int(0x00406d7c, 0)
        game.cleanup()

    return history


def main():
    import argparse
    p = argparse.ArgumentParser(description="Multi-instance AI Runner")
    p.add_argument("-n", "--instances", type=int, default=5,
                   help="Number of parallel game instances")
    p.add_argument("--ai", default="ai_beam", help="AI algorithm")
    p.add_argument("--runs", type=int, default=2,
                   help="Runs per instance (total = instances × runs)")
    args = p.parse_args()

    total_runs = args.instances * args.runs
    logger.info(
        f"Starting {args.instances} instances × {args.runs} runs = "
        f"{total_runs} total | AI: {args.ai}"
    )

    # Compute grid layout — nearest square
    import math
    cols = math.ceil(math.sqrt(args.instances))
    rows = math.ceil(args.instances / cols)

    all_history = []
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=args.instances) as pool:
        futures = {}
        for i in range(args.instances):
            col = i % cols
            row = i // cols
            f = pool.submit(run_instance, i, args.ai, args.runs, col, row, cols, rows)
            futures[f] = i
            time.sleep(0.3)  # stagger launches so windows don't overlap
        for future in as_completed(futures):
            result = future.result()
            all_history.extend(result)

    elapsed = time.time() - start_time
    all_history.sort(key=lambda r: r["survival_s"], reverse=True)

    # Print summary
    if not all_history:
        print("\n  No runs completed — all instances failed.")
        return

    times = [r["survival_s"] for r in all_history]
    bullets = [r["max_bullets"] for r in all_history]
    sorted_times = sorted(times)
    n = len(sorted_times)

    print("\n" + "=" * 70)
    print(f"  MULTI-RUNNER SUMMARY — {args.instances} instances × {args.runs} runs")
    print(f"  Total: {n} runs in {elapsed:.0f}s | AI: {args.ai}")
    print(f"  Best:  {max(times):.1f}s  Worst: {min(times):.1f}s  "
          f"Avg: {sum(times)/n:.1f}s  Median: {sorted_times[n//2]:.1f}s")
    print(f"  P90: {sorted_times[int(n*0.9)]:.1f}s  "
          f"P75: {sorted_times[int(n*0.75)]:.1f}s  "
          f"P25: {sorted_times[int(n*0.25)]:.1f}s")
    print(f"  Max bullets: {max(bullets)}")
    print("-" * 70)
    for r in all_history[:15]:
        tstr = ",".join(f"T{t}={c}" for t,c in sorted(r.get("types",{}).items()))
        pstr = ",".join(f"P{p}={c}" for p,c in sorted(r.get("patterns",{}).items()))
        print(f"  I{r['instance']} R{r['run']:>2}: {r['survival_s']:>6.1f}s "
              f"B:{r['max_bullets']:>3} Grz:{r.get('graze_max',0):>3} "
              f"[{tstr}] [{pstr}]")
    if n > 15:
        print(f"  ... and {n - 15} more")
    print("=" * 70)

    # Save
    os.makedirs("logs", exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join("logs", f"multi_{args.ai}_{ts}.json")
    with open(path, "w") as f:
        json.dump({"ai": args.ai, "instances": args.instances,
                    "elapsed_s": elapsed, "runs": all_history}, f, indent=2)
    logger.info(f"Saved → {path}")


if __name__ == "__main__":
    main()
