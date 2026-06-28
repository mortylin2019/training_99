"""
runner.py — Connects GameControl (memory I/O) → AI algorithm → game.
Full automation: detects title / game-over / ranking screens, auto-advances.

Usage:
    python hijack_tools/runner.py                     # 10 runs, ai_direct
    python hijack_tools/runner.py --runs 20           # 20 runs
    python hijack_tools/runner.py --runs 0            # infinite
    python hijack_tools/runner.py --ai my_algo        # swap algorithm
"""

import time
import sys
import json
import os
from datetime import datetime
from loguru import logger

try:
    from game_control import GameControl
    import keyboard as kbd
except ImportError:
    from hijack_tools.game_control import GameControl
    import hijack_tools.keyboard as kbd

logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("logs/runner.log", rotation="10 MB", retention="5 days",
           compression="zip", level="DEBUG")

STATE_TITLE, STATE_RESULT, STATE_RANKING = 0, 5, 6


def load_ai(name):
    if name == "ai_direct":
        from ai_direct import SuperiorAI
        return SuperiorAI
    raise ValueError(f"Unknown AI: {name}")


def run(ai_name="ai_direct", max_runs=10):
    game = GameControl()
    if not game.launch_game():
        logger.error("Failed to launch game")
        return

    AI = load_ai(ai_name)
    ai = AI(vel_table=game.vel_table, accel_table=game.accel_table)

    mode = f"{max_runs} runs" if max_runs > 0 else "infinite"
    logger.info(f"Runner — AI:{ai_name} — {mode} — Ctrl+C to stop.")

    history = []
    run_count = 0
    in_run = False
    max_bullets = 0
    run_frames = 0
    last_log = 0.0
    last_screen = -1

    try:
        while True:
            state = game.get_game_state()
            is_playing = game.is_playing()
            is_dead = game.is_game_over()

            # ── New run ──
            if is_playing and not is_dead and not in_run:
                in_run = True
                max_bullets = 0
                run_frames = 0
                run_count += 1
                logger.success(f"=== RUN {run_count} START ===")

            # ── Run ended ──
            if in_run and (not is_playing or is_dead):
                in_run = False
                ms = game.get_survival_ms()
                frames = game.get_game_time()
                mult = game.get_score_multiplier() or 1
                history.append({
                    "run": run_count,
                    "survival_ms": ms,
                    "survival_s": ms / 1000.0,
                    "frames": frames,
                    "multiplier": mult,
                    "max_bullets": max_bullets,
                })
                logger.success(
                    f"=== DEAD | Run {run_count} | {ms}ms ({ms/1000:.1f}s) | "
                    f"Frames:{frames} | MaxB:{max_bullets} ==="
                )
                game.write_int(0x00406d7c, 0)
                time.sleep(0.3)

                if max_runs > 0 and run_count >= max_runs:
                    logger.success(f"All {max_runs} runs complete.")
                    break

            # ── Auto-advance screens ──
            if not is_playing and not in_run:
                game.write_int(0x00406d7c, 0)

                if state != last_screen:
                    screen_names = {0: "Title", 5: "Result", 6: "Ranking"}
                    logger.debug(f"Screen: {screen_names.get(state, state)}")
                    last_screen = state

                game.press_enter()
                time.sleep(0.15)
                continue

            # ── Gameplay ──
            if in_run and is_playing:
                px, py = game.get_player_pos()
                bullets = game.get_bullets()
                active = [b for b in bullets if b.angle_index != 0xFF]

                run_frames += 1
                if len(active) > max_bullets:
                    max_bullets = len(active)

                bits = ai.decide(px, py, active)
                game.write_int(0x00406d7c, bits)

                now = time.time()
                if now - last_log > 2.0:
                    pat = game.get_next_pattern()
                    grz = game.get_active_near()
                    types = {}
                    for b in active:
                        types[b.type] = types.get(b.type, 0) + 1
                    tstr = " ".join(f"T{t}={c}" for t, c in sorted(types.items()))
                    logger.info(
                        f"R{run_count} P:{px:>3},{py:>3} B:{len(active):>3} [{tstr}] "
                        f"Pat:{pat} Grz:{grz} → {kbd.get_key_name(bits):>8} | {run_frames}tk"
                    )
                    last_log = now

    except KeyboardInterrupt:
        game.write_int(0x00406d7c, 0)
        logger.info("Stopped by user.")
    finally:
        game.cleanup()

    if history:
        print_summary(history)
        save_history(history, ai_name)


def print_summary(history):
    print("\n" + "=" * 60)
    print("  RUN SUMMARY")
    print("=" * 60)
    times = [r["survival_s"] for r in history]
    bullets = [r["max_bullets"] for r in history]
    print(f"  Runs:        {len(history)}")
    print(f"  Best:        {max(times):.1f}s")
    print(f"  Worst:       {min(times):.1f}s")
    print(f"  Avg:         {sum(times)/len(times):.1f}s")
    print(f"  Max bullets: {max(bullets)}")
    print("-" * 60)
    for r in history:
        bar = "#" * int(r["survival_s"])
        print(f"  Run {r['run']:>2}: {r['survival_s']:>6.1f}s  {bar}")
    print("=" * 60)


def save_history(history, ai_name):
    os.makedirs("logs", exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join("logs", f"history_{ai_name}_{ts}.json")
    with open(path, "w") as f:
        json.dump({"ai": ai_name, "runs": history}, f, indent=2)
    logger.info(f"History saved → {path}")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="AI Runner for Training 99")
    p.add_argument("--ai", default="ai_direct", help="AI algorithm module")
    p.add_argument("--runs", type=int, default=10,
                   help="Number of runs (0=infinite)")
    args = p.parse_args()
    run(args.ai, args.runs)
