# 特訓９９ — Reverse Engineering & AI Hijack

Reverse-engineered Japanese bullet-hell survival game. Python AIs attach to the live process via `ReadProcessMemory`/`WriteProcessMemory`, read bullet positions, and play autonomously by writing direction bitmasks directly to the game's input register.

<p align="center">
  <video src="demo/ai_beam_153s.mp4" controls width="100%"></video>
  <br><i>ai_beam — 153.7s survival on Normal difficulty</i>
  <br><sub>also on <a href="https://youtu.be/qBO9xRoYYME">YouTube</a></sub>
</p>

## AI Performance (Simulator, Normal Difficulty, 50s Cap)

| AI | Avg | Best | Worst | Approach |
|---|---|---|---|---|
| `BasicAI` | 6.8s | 15.0s | 4.0s | 1/r² repulsion field, no lookahead |
| `ai_beam` (width=50) | 38.5s | 50.0s | 3.2s | Beam search, 80-frame lookahead |
| **`ai_nn` (NNBoostedBeam)** | **42.9s** | **50.0s** | **11.6s** | NN escape-path protection + beam search |
| `ai_nn_greedy` | 19.6s | 41.3s | 3.2s | NN single-frame policy (no search) |

## Quick Start

### Simulator (any OS, no game binary needed)
```bash
pip install numpy numba torch tqdm
python -m hijack_tools.simulator.runner --ai ai_beam --runs 50
```

Available AIs: `ai_basic`, `ai_beam`, `ai_nn`, `ai_nn_greedy`

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
Each bullet exerts a repulsive force `F = 1/r²`. Sum all force vectors → move in the net repulsion direction. Zero lookahead, zero velocity prediction. Pure reactive physics.

### `ai_beam` — Time-Space Beam Search
Precomputes 80-frame bullet trajectories via linear velocity extrapolation. At each depth step, evaluates 9×K candidate positions with inverse-square danger scoring + wall penalty + center pull. Keeps top K=50 paths. Intermediate frames checked for fatal collisions between beam steps. Finds escape routes through bullet convergence patterns that simpler AIs miss.

### `ai_nn` (NNBoostedBeam) — Neural-Guided Beam Search
Runs beam search TWICE per frame: once normally, once with the NN's preferred escape move forced at depth 0. Compares intermediate danger scores of both paths. The NN (trained on 769K beam search demonstrations) sees the escape gap from a single frame — beam search prunes it at depth 2 because the danger hasn't manifested yet. The forced beam lets the escape path survive until depth 15+ where future scores reveal its value.

**Model**: DeepSet attention-pooling (77K params) with relative bullet positions. 72% validation accuracy on beam search move prediction. Policy head outputs 9-way move probabilities; value head estimates survival time.

## Architecture

| `hijack_tools/` | AI bots, game memory interface |
| `hijack_tools/simulator/` | Faithful offline game replica (same RNG, physics, patterns) |
| `tools/` | Reverse engineering utilities, NN training pipeline |
| `reverse_engineering_ref/` | Ghidra decompilation, assembly dumps, memory maps |
| `doc/` | Human-readable game mechanics analysis |

## Key Technical Details

- **Game**: 32-bit Windows, ~80 FPS, 304×224 playfield
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
