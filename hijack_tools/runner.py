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
import threading
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
    if name == "ai_beam":
        from ai_beam import BeamAI
        return BeamAI
    if name == "ai_numba":
        from ai_beam import BeamAI
        return BeamAI  # legacy alias
    raise ValueError(f"Unknown AI: {name}")


def run(ai_name="ai_direct", max_runs=10):
    game = GameControl()
    if not game.launch_game():
        logger.error("Failed to launch game")
        return

    AI = load_ai(ai_name)
    ai = AI(vel_table=game.vel_table, accel_table=game.accel_table)

    # Warm up JIT before game starts
    from bullet_data import Bullet
    fake = [Bullet(raw_x=0x8000, raw_y=0x4000, angle_index=i, active=1,
                   type=0, timer=0, index=0, vx=0, vy=0) for i in range(20)]
    for _ in range(3):
        ai.decide(152, 44, fake)

    mode = f"{max_runs} runs" if max_runs > 0 else "infinite"
    logger.info(f"Runner — AI:{ai_name} — {mode} — Ctrl+C to stop.")

    history = []
    run_count = 0
    in_run = False
    max_bullets = 0
    run_frames = 0
    last_log = 0.0
    last_screen = -1

    # ── Bits→movement lookup + prediction tracker ──
    _BITS_MAP = {0:(0,0), 1:(-1,0), 8:(1,0), 2:(0,-1), 4:(0,1),
                 3:(-1,-1), 5:(-1,1), 10:(1,-1), 12:(1,1)}
    _pred_px = _pred_py = None
    _lag_count = 0
    _state = {"px": 152, "py": 44, "active": [], "ready": False}
    _lock = threading.Lock()
    _stop = threading.Event()

    def _reader():
        while not _stop.is_set() and game.process_handle:
            px, py = game.get_player_pos()
            active = [b for b in game.get_bullets() if b.angle_index != 0xFF]
            with _lock:
                _state["px"] = px; _state["py"] = py
                _state["active"] = active; _state["ready"] = True
            _stop.wait(0.005)  # ~200 Hz, game runs at 80 Hz

    _thread = threading.Thread(target=_reader, daemon=True)
    _thread.start()
    for _ in range(100):  # wait for first data
        with _lock:
            if _state["ready"]: break
        time.sleep(0.01)

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
                _pred_px = _pred_py = None
                logger.success(f"=== RUN {run_count} START ===")

            # ── Run ended ──
            if in_run and (not is_playing or is_dead):
                in_run = False
                
                # Save pre-death snapshot for analysis
                try:
                    with open(f'logs/death_r{run_count}.json', 'w') as f:
                        json.dump(_last_snapshot, f)
                    nbullets = len(_last_snapshot['bullets'])
                    logger.debug(f'Saved death snapshot: {nbullets} bullets')
                except NameError:
                    pass
                except Exception as e:
                    logger.warning(f'Failed to save death snapshot: {e}')
                
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

            # ── Gameplay (reads latest state from background thread) ──
            if in_run and is_playing:
                with _lock:
                    px, py = _state["px"], _state["py"]
                    active = _state["active"]

                # Compare actual position to our prediction from last frame
                if _pred_px is not None:
                    pdx = px - _pred_px
                    pdy = py - _pred_py
                    if abs(pdx) > 1 or abs(pdy) > 1:
                        _lag_count += 1

                run_frames += 1
                if len(active) > max_bullets:
                    max_bullets = len(active)

                # ── Bullet prediction accuracy ──
                _pred_err = 0.0
                if active and hasattr(ai, '_last_bullet'):
                    lb = ai._last_bullet
                    for b in active:
                        if b.angle_index == lb['ang'] and b.type == lb['type']:
                            pred_x = lb['px'] + lb['vx']
                            pred_y = lb['py'] + lb['vy']
                            _pred_err = ((b.x-pred_x)**2+(b.y-pred_y)**2)**0.5
                            break
                if active:
                    b0 = active[0]
                    idx = b0.angle_index & 63
                    import struct
                    vdata = game.read_memory(0x00405d74 + idx*12, 8)
                    rvx, rvy = struct.unpack('<ii', vdata)
                    ai._last_bullet = {
                        'ang': b0.angle_index, 'type': b0.type,
                        'px': b0.x, 'py': b0.y,
                        'vx': rvx/64.0, 'vy': rvy/64.0
                    }

                bits = ai.decide(px, py, active)
                game.write_int(0x00406d7c, bits)

                # ── Save pre-death snapshot ──
                _last_snapshot = {
                    'px': px, 'py': py,
                    'bullets': [(b.raw_x, b.raw_y, b.angle_index, b.type,
                                 b.timer, b.counter, b.vx, b.vy) for b in active],
                    'bits': bits
                }

                # Predict where player SHOULD be next frame
                dx, dy = _BITS_MAP.get(bits, (0, 0))
                _pred_px = px + dx
                _pred_py = py + dy

                now = time.time()
                if now - last_log > 2.0:
                    pat = game.get_next_pattern()
                    grz = game.get_active_near()
                    types = {}
                    for b in active:
                        types[b.type] = types.get(b.type, 0) + 1
                    tstr = " ".join(f"T{t}={c}" for t, c in sorted(types.items()))
                    lag_str = f" | LAG:{_lag_count}" if _lag_count > 0 else ""
                    pred_str = f" | PRED_ERR:{_pred_err:.1f}px" if _pred_err > 1.0 else ""
                    logger.info(
                        f"R{run_count} P:{px:>3},{py:>3} B:{len(active):>3} [{tstr}] "
                        f"Pat:{pat} Grz:{grz} → {kbd.get_key_name(bits):>8} | {run_frames}tk{lag_str}{pred_str}"
                    )
                    last_log = now
                    _lag_count = 0

    except KeyboardInterrupt:
        game.write_int(0x00406d7c, 0)
        logger.info("Stopped by user.")
    finally:
        _stop.set()
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
    st = sorted(times)
    n = len(st)
    print(f"  Runs:        {n}")
    print(f"  Best:        {max(times):.1f}s")
    print(f"  Worst:       {min(times):.1f}s")
    print(f"  Avg:         {sum(times)/n:.1f}s")
    print(f"  Median:      {st[n//2]:.1f}s")
    print(f"  P90: {st[int(n*0.9)]:.1f}s  P75: {st[int(n*0.75)]:.1f}s  P25: {st[int(n*0.25)]:.1f}s")
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
