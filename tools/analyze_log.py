#!/usr/bin/env python3
"""
Analyze runner log files — extract control quality metrics.

Usage:
  python tools/analyze_log.py logs/runner.log
  python tools/analyze_log.py logs/runner.log --run R4
  python tools/analyze_log.py logs/ --all  # scan all runner.log*
"""
import re, sys, glob, argparse
from collections import defaultdict
import numpy as np

# Log line pattern:
# R4 P:152, 44 B: 29 [T0=29] Pat:0 Grz:0 →     DOWN | 1tk | PRED_ERR:155.3px
LINE_RE = re.compile(
    r'(R\d+)\s+P:\s*(-?\d+),\s*(-?\d+)\s+B:\s*(-?\d+)'
    r'.*?Pat:(-?\d+)\s+Grz:(-?\d+).*?→\s+(\S+)'
    r'\s*\|\s*(-?\d+)tk'
    r'(?:\s*\|\s*LAG:(-?\d+))?'
    r'(?:\s*\|\s*PRED_ERR:([\d.]+)px)?'
)


def parse_log(path, run_filter=None):
    """Parse runner log files, return list of frames."""
    frames = []
    if path.endswith('.zip'):
        import zipfile, io
        with zipfile.ZipFile(path) as zf:
            for name in zf.namelist():
                with zf.open(name) as f:
                    frames.extend(_parse_lines(io.TextIOWrapper(f), run_filter))
    else:
        with open(path, errors='ignore') as f:
            frames.extend(_parse_lines(f, run_filter))
    return frames


def _parse_lines(f, run_filter):
    frames = []
    for line in f:
        m = LINE_RE.search(line)
        if not m:
            continue
        run = m.group(1)
        if run_filter and run != run_filter:
            continue
        frames.append({
            'run': run,
            'px': int(m.group(2)), 'py': int(m.group(3)),
            'bullets': int(m.group(4)),
            'pattern': int(m.group(5)),
            'graze': int(m.group(6)),
            'direction': m.group(7).strip(),
            'tick': int(m.group(8)),
            'lag': int(m.group(9)) if m.group(9) else 0,
            'pred_err': float(m.group(10)) if m.group(10) else None,
        })
    return frames


def analyze(frames, label=""):
    """Compute control quality metrics from parsed frames."""
    if not frames:
        print("No frames found.")
        return

    runs = sorted(set(f['run'] for f in frames))
    print(f"\n{'='*60}")
    print(f"  Control Quality Report  {label}")
    print(f"{'='*60}")
    print(f"  Runs: {len(runs)} ({', '.join(runs[:5])}{'...' if len(runs)>5 else ''})")
    print(f"  Frames: {len(frames)}")

    # ── LAG ──
    lag_frames = [f for f in frames if f['lag'] > 0]
    lags = [f['lag'] for f in lag_frames]
    print(f"\n  ── Frame Drop (LAG) ──")
    print(f"  Frames with LAG: {len(lag_frames)}/{len(frames)} ({100*len(lag_frames)/len(frames):.1f}%)")
    if lags:
        print(f"  LAG per event:   min={min(lags)} max={max(lags)} avg={np.mean(lags):.1f} median={np.median(lags):.0f}")
    print(f"  Total LAG frames: {sum(lags)}")
    print(f"  Effective FPS:    {80 * (1 - sum(lags)/len(frames)):.1f}")

    # ── Direction changes ──
    dirs = [f['direction'] for f in frames]
    changes = sum(1 for i in range(1, len(dirs)) if dirs[i] != dirs[i-1])
    reversals = 0
    opposites = {
        'LEFT': 'RIGHT', 'RIGHT': 'LEFT',
        'UP': 'DOWN', 'DOWN': 'UP',
        'UP-LEFT': 'DOWN-RIGHT', 'DOWN-RIGHT': 'UP-LEFT',
        'UP-RIGHT': 'DOWN-LEFT', 'DOWN-LEFT': 'UP-RIGHT',
    }
    for i in range(1, len(dirs)):
        if opposites.get(dirs[i]) == dirs[i-1]:
            reversals += 1

    print(f"\n  ── Direction Stability ──")
    print(f"  Changes:  {changes}/{len(dirs)-1} ({100*changes/max(len(dirs)-1,1):.1f}%)")
    print(f"  Reversals: {reversals}/{len(dirs)-1} ({100*reversals/max(len(dirs)-1,1):.1f}%)")
    avg_dir_hold = np.mean([len(list(g)) for _, g in __import__('itertools').groupby(dirs)])
    print(f"  Avg frames between changes: {avg_dir_hold:.1f}")

    # Direction distribution
    dir_counts = defaultdict(int)
    for d in dirs:
        dir_counts[d] += 1
    print(f"  Direction distribution:")
    for d, c in sorted(dir_counts.items(), key=lambda x: -x[1])[:5]:
        print(f"    {d:>12s}: {c:4d} ({100*c/len(dirs):.1f}%)")

    # ── Movement ──
    xs = [f['px'] for f in frames]
    ys = [f['py'] for f in frames]
    distances = []
    for i in range(1, len(frames)):
        dt = frames[i]['tick'] - frames[i-1]['tick']
        if dt > 0:
            dx = xs[i] - xs[i-1]
            dy = ys[i] - ys[i-1]
            distances.append((dx*dx + dy*dy)**0.5 / dt)

    print(f"\n  ── Movement Range ──")
    print(f"  X: {min(xs)} to {max(xs)}  (span {max(xs)-min(xs)}px, {100*(max(xs)-min(xs))/304:.0f}% of screen)")
    print(f"  Y: {min(ys)} to {max(ys)}  (span {max(ys)-min(ys)}px, {100*(max(ys)-min(ys))/224:.0f}% of screen)")
    if distances:
        print(f"  Avg speed: {np.mean(distances):.2f} px/tick (diagonal=1.4 max)")

    # ── Per-pattern breakdown ──
    pat_frames = defaultdict(list)
    for f in frames:
        pat_frames[f['pattern']].append(f)

    print(f"\n  ── Per-Pattern Stability ──")
    for pat in sorted(pat_frames):
        pdirs = [f['direction'] for f in pat_frames[pat]]
        pchanges = sum(1 for i in range(1, len(pdirs)) if pdirs[i] != pdirs[i-1])
        prevs = 0
        for i in range(1, len(pdirs)):
            if opposites.get(pdirs[i]) == pdirs[i-1]:
                prevs += 1
        plags = [f['lag'] for f in pat_frames[pat]]
        print(f"    Pat {pat:>2}: {len(pat_frames[pat]):4d} frames | "
              f"change {100*pchanges/max(len(pdirs)-1,1):.0f}% | "
              f"reversal {100*prevs/max(len(pdirs)-1,1):.0f}% | "
              f"LAG avg {np.mean(plags):.1f}")

    # ── Prediction error ──
    pred_errs = [f['pred_err'] for f in frames if f['pred_err'] is not None]
    if pred_errs:
        print(f"\n  ── Prediction Error ──")
        print(f"  Logged errors: {len(pred_errs)}")
        print(f"  Max: {max(pred_errs):.1f}px  Avg: {np.mean(pred_errs):.1f}px")
        big = [e for e in pred_errs if e > 5]
        if big:
            print(f"  Large errors (>5px): {len(big)} ({100*len(big)/len(pred_errs):.1f}%)")

    # ── Summary score ──
    change_rate = 100*changes/max(len(dirs)-1, 1)
    reversal_rate = 100*reversals/max(len(dirs)-1, 1)
    lag_rate = 100*len(lag_frames)/len(frames)
    print(f"\n  ── Summary ──")
    print(f"  Direction change: {change_rate:.0f}%  Reversal: {reversal_rate:.0f}%  LAG: {lag_rate:.1f}%")
    if change_rate > 50:
        print(f"  ⚠  High direction change rate — AI oscillates strategy")
    if reversal_rate > 15:
        print(f"  ⚠  High reversal rate — AI wastes movement backtracking")
    if lag_rate > 5:
        print(f"  ⚠  High LAG — AI can't keep up with frame rate")
    if change_rate < 30 and reversal_rate < 10 and lag_rate < 3:
        print(f"  ✓  Good control quality")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Analyze runner log quality")
    p.add_argument("path", help="Log file or directory")
    p.add_argument("--run", help="Filter to specific run (e.g. R4)")
    p.add_argument("--all", action="store_true", help="Scan all runner.log* files")
    args = p.parse_args()

    paths = []
    if args.all or os.path.isdir(args.path):
        dir_path = args.path if os.path.isdir(args.path) else os.path.dirname(args.path)
        paths = sorted(glob.glob(os.path.join(dir_path, "runner.log*")))
    else:
        paths = [args.path]

    all_frames = []
    for p in paths:
        if os.path.exists(p):
            all_frames.extend(parse_log(p, run_filter=args.run))

    if not all_frames:
        print(f"No frames found in: {args.path}")
        sys.exit(1)

    analyze(all_frames, label=os.path.basename(args.path))
