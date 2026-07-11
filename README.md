# 特訓９９ — Reverse Engineering & AI Hijack

Reverse-engineered Japanese bullet-hell survival game. Python AIs attach to the live process via `ReadProcessMemory`/`WriteProcessMemory`, read bullet positions, and play autonomously by writing direction bitmasks directly to the game's input register.

<p align="center">
  <a href="https://youtu.be/qBO9xRoYYME">
    <img src="assets/demo_thumb.jpg" width="480" alt="▶ Watch Demo">
  </a>
  <br><b>▶ Watch Demo</b> — 153.7s survival, Normal difficulty
  <br><i>ai_beam dodging 50+ bullets — beam search with 160-frame lookahead</i>
</p>

## Why

I used to write programs to play games automatically — it was my way of learning programming and machine learning. 特訓９９ is one of the games I played when I was young. It would be fun if I could write a program to play it, but at the time it was too difficult for me.

Now with all the new AI tools, I can reverse-engineer the EXE, attach real-time memory monitoring for game state, and write sophisticated algorithms within a reasonable amount of time.

## AI Performance (Simulator, Normal Difficulty, 30 runs)

| AI | Med | Avg | Min | Max | Approach |
|---|---|---|---|---|---|
| `ai_basic` | 8.8s | 10.3s | 2.8s | 21.1s | 1/r² repulsion + wall avoidance + center pull |
| `ai_beam` (W=200, CE=4) | 69.6s | 71.9s | 7.4s | 148.5s | Beam search, 160-frame lookahead |

> **`ai_nn`** (neural-guided beam search) is ongoing work — DeepSet attention model trained on beam search demonstrations. See `tools/train_nn.py`.

## Quick Start

### Simulator (any OS, no game binary needed)
```bash
pip install numpy numba torch tqdm
python -m hijack_tools.simulator.runner --ai ai_beam --runs 50
```

Available AIs: `ai_basic`, `ai_beam`, `ai_mcts`, `ai_nn`, `ai_nn_greedy`

### Compare AIs
```bash
python tools/bench_compare.py --runs 10 --ai ai_basic,ai_beam
```

### Live Game (Windows only, requires `raw/99.exe`)
```bash
pip install pywin32 numpy loguru
python hijack_tools/runner.py --ai ai_beam --runs 10
```

### Train Your Own NN
```bash
# 1. Generate training data (resumable, crash-safe)
python tools/gen_training_data.py --seeds 1000 --width 50 --workers 16

# 2. Combine shards
python tools/gen_training_data.py --combine

# 3. Train (early stopping, cosine annealing, val split)
python tools/train_nn.py --epochs 100 --batch_size 1024
```

## How It Works

```
┌─────────────┐    ReadProcessMemory     ┌──────────────┐
│   99.exe    │◄─────────────────────────│  GameControl  │
│  (32-bit)   │─────────────────────────►│  (Python)     │
│             │   WriteProcessMemory     │              │
└─────────────┘   (G_InputState=0x6d7c) └──────┬───────┘
                                                │
                                         ┌──────▼───────┐
                                         │   AI Engine  │
                                         │ px,py,bullets│
                                         │   → bitmask  │
                                         └──────────────┘
```

The AI reads player position, active bullets, and game state from memory. It decides a movement direction and writes the bitmask (`1=LEFT, 2=UP, 4=DOWN, 8=RIGHT`) directly to `0x00406d7c`. The game reads this register each frame and moves the player 1px. No keyboard simulation, no Windows messages — pure process hijacking.

## AI Algorithms

### `ai_basic` — 1/r² Repulsion Field

Each bullet exerts a repulsive force `F = 1/r²`. Wall edges exert a 1/d² repulsion to prevent wall-hugging deaths. A gentle center-pull force prevents drifting into corners. Sum all force vectors → move in the net repulsion direction. Zero lookahead, zero velocity prediction. Pure reactive physics. O(9+N) per frame.

### `ai_beam` — Time-Space Beam Search

Beam search treats the game as a tree search over time: "if I move in direction D now, where will every bullet be 160 frames from now, and how dangerous is that position?"

#### How It Works

**1. Bullet Trajectory Prediction**

Before the beam search starts, all active bullets have their future positions precomputed 120 frames ahead via linear velocity extrapolation. For each bullet at angle `θ`, the game uses a 64-entry velocity lookup table (`VEL_TABLE[θ] = (vx, vy)`). The prediction is exact for Type 0 (normal) and Type 3 (accelerating) bullets — they move at constant velocity. Type 1 (homing) and Type 2 (bounce) bullets can change direction, but the linear approximation works well enough for scoring.

**2. Multi-Beam Search**

Instead of one beam, 9 independent beams run in parallel — each locked to a different first move (STOP, LEFT, RIGHT, UP, DOWN, and 4 diagonals). This prevents the single winning move from dominating early and missing escape paths that only reveal their value later. Each beam:

- **Depth**: 40 beam steps × CE=4 frames/step = **160 frames** of temporal coverage (~2.5 seconds)
- **Width**: W=200 — keeps the top 200 candidate positions at each depth step
- **Branching**: At each step, generates 9 candidate next positions (all move directions)

**3. Scoring Function**

Each candidate position `(px, py)` at depth `t` is scored against all active bullet positions `(bx, by)`:

```
danger = Σ  DANGER_BASE / dx² + dy²       (inverse-square, per bullet)
       + WALL_PENALTY * max(0, 1 - dist/WALL_MARGIN)²  (wall danger)
       - CENTER_PULL * dist_to_center²     (center reward)
```

- `DANGER_BASE = 3000` — makes even distant bullets contribute meaningfully
- `WALL_PENALTY = 5000`, `WALL_MARGIN = 20px` — steep penalty near edges
- `CENTER_PULL = 0.3` — gentle bias toward center, prevents corner camping
- `SAFETY_MARGIN = 2px` — extra clearance around the 11×10 hitbox

Bullets inside the hitbox (including safety margin) assign `COLLISION_VAL = 1e8` — instant discard.

**4. Early Exit Optimization**

At each depth step, candidates are sorted by cumulative danger. If a candidate's danger exceeds the current best candidate's danger by `EARLY_EXIT_BUFFER = 50000`, the bullet loop exits early — that candidate can't possibly win. This is the primary speed optimization, cutting evaluation time by ~40% in dense patterns.

**5. Why CE=4 (Check Every 4 frames)**

Coarser stepping (evaluating positions every 4th frame instead of every frame) provides two benefits:

- **Implicit smoothing**: Small bullet movements between check frames average out, reducing noise in the danger signal
- **Extended temporal range**: 40 steps × CE=4 = 160 frames of coverage vs 40 steps × CE=1 = 40 frames

CE=1 would give finer-grained evaluation but half the lookahead distance. The 160-frame range is critical — beam search sees bullet convergence patterns that simpler AIs react to 2 seconds too late.

**6. Path Selection**

After all 9 beams complete, the winning first move is selected: the move whose beam achieved the lowest cumulative danger across its best path. This is the direction the AI moves for the next frame. The whole process repeats every frame (~2.7ms per decision).

#### Why Beam Search Wins

The game's core challenge is spatial-temporal reasoning: finding gaps in moving bullet patterns before they close. Beam search solves this by **explicitly simulating the future** — it doesn't guess or learn, it computes where everything will be and finds the path through.

The 160-frame lookahead means it sees escape routes through dense patterns that would take a human (or a reactive AI) 2+ seconds to recognize. Combined with inverse-square danger scoring, it naturally prefers positions with more clearance, trading slight danger now for safety later.

### `ai_nn` (NNBoostedBeam) — Ongoing Work

Neural-guided beam search. A DeepSet attention-pooling model (77K params) trained on beam search demonstrations predicts which escape direction the beam search will choose. The NN runs the beam search twice: once normally, once with the NN's predicted move forced at depth 0. If the forced path scores better at depth 15+, the NN's move is used — it saw the escape gap before beam search pruned it.

Training: `python tools/gen_training_data.py --seeds 1000 --workers 16` then `python tools/train_nn.py --epochs 100`.

## Architecture

| `hijack_tools/` | AI bots, game memory interface |
| `hijack_tools/simulator/` | Faithful offline game replica (same RNG, physics, patterns) |
| `tools/` | Reverse engineering utilities, NN training pipeline |
| `reverse_engineering_ref/` | Ghidra decompilation, assembly dumps, memory maps |
| `doc/` | Human-readable game mechanics analysis |

## Key Technical Details

- **Game**: 32-bit Windows, ~62.5 FPS (Standard), 304×224 playfield
- **Player hitbox**: 11×10 px (asymmetric: 2-12 X, 0-9 Y offset)
- **Movement**: 1 px/frame, diagonals not normalized
- **Bullets**: 300-entity array at `0x00406e10`, 15 bytes each, 4 types (normal/homing/bounce/accelerating)
- **Input**: Write bitmask to `G_InputState` (`0x00406d7c`). NEVER `SendMessage` for movement, NEVER direct position write (teleport cheating).
- **RNG**: LCG `state = state × 0x343FD + 0x269EC3`
- **Simulator**: Verified 1105/1105 instruction-level tests against 99.exe via radare2 ESIL

## Tests
```bash
python tests/test_functions.py        # 30 unit tests (no binary needed)
python tests/test_integration.py      # 20 integration tests
python tests/test_cross_validate.py   # Python vs real binary (Windows only)
```
