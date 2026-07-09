"""
ai_nn.py — Neural Network guided AI players.

NNGreedyAI:  Direct NN policy → move (72% acc, <1ms/frame).
NNMCTSAI:   Depth-1 batched MCTS with NN value + UCT (robust, ~3ms/frame).
NNFallbackAI: NN safety net over beam search (best of both, ~10ms/frame).

Model: DeepSet attention-pooling + BatchNorm trunk → 9-way policy + survival value.
"""
import os
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

try:
    from algo_config import (
        MOVES, BITS, N_ACTIONS, SPEED,
        SCR_W, SCR_H, CTR_X, CTR_Y,
        BEAM_DEPTH, BEAM_WIDTH, CHECK_EVERY,
        HIT_X1, HIT_X2, HIT_Y1, HIT_Y2,
    )
except ImportError:
    from hijack_tools.algo_config import (
        MOVES, BITS, N_ACTIONS, SPEED,
        SCR_W, SCR_H, CTR_X, CTR_Y,
        BEAM_DEPTH, BEAM_WIDTH, CHECK_EVERY,
        HIT_X1, HIT_X2, HIT_Y1, HIT_Y2,
    )

# Try dual-path import for simulator tables
try:
    from simulator.tables import VEL_TABLE
except ImportError:
    from hijack_tools.simulator.tables import VEL_TABLE

# Try dual-path import for BeamAI base class
try:
    from ai_beam import BeamAI, _beam_search, _score_pos
except ImportError:
    from hijack_tools.ai_beam import BeamAI, _beam_search, _score_pos

# Precomputed velocity lookup (matches train_nn.py)
_VEL = np.array([(VEL_TABLE[i][0] / 64.0, VEL_TABLE[i][1] / 64.0)
                 for i in range(64)], dtype=np.float32)

BITS_TO_IDX = {b: i for i, b in enumerate(BITS)}
IDX_TO_BITS = {i: b for i, b in enumerate(BITS)}


# ── Model architecture (mirrors train_nn.py — must match checkpoint) ───────────

class DeepSet(nn.Module):
    def __init__(self, bullet_dim=5, hidden=128, out_dim=64):
        super().__init__()
        self.bullet_enc = nn.Sequential(
            nn.Linear(bullet_dim, hidden), nn.ReLU(),
            nn.Linear(hidden, hidden), nn.ReLU(),
            nn.Linear(hidden, out_dim),
        )
        self.scorer = nn.Linear(out_dim, 1)

    def forward(self, bullets, mask):
        B, N, _ = bullets.shape
        x = self.bullet_enc(bullets.view(B * N, -1)).view(B, N, -1)
        scores = self.scorer(x).squeeze(-1)
        mask_bool = mask.bool()
        scores = scores.masked_fill(~mask_bool, float('-inf'))
        weights = F.softmax(scores, dim=1)
        weights = torch.where(weights.isnan(), torch.zeros_like(weights), weights)
        x = x * weights.unsqueeze(-1)
        return x.sum(dim=1)


class PolicyValueNet(nn.Module):
    def __init__(self, max_bullets=300, bullet_dim=5, player_dim=2):
        super().__init__()
        self.deepset = DeepSet(bullet_dim=bullet_dim)
        self.trunk = nn.Sequential(
            nn.Linear(64 + player_dim, 256), nn.BatchNorm1d(256), nn.ReLU(),
            nn.Linear(256, 128), nn.BatchNorm1d(128), nn.ReLU(),
        )
        self.policy_head = nn.Linear(128, 9)
        self.value_head = nn.Linear(128, 1)

    def forward(self, bullets, mask, player):
        enc = self.deepset(bullets, mask)
        x = torch.cat([enc, player], dim=1)
        x = self.trunk(x)
        return self.policy_head(x), self.value_head(x).squeeze(-1)


# ── NN loading ─────────────────────────────────────────────────────────────────

def load_nn_model(path="training_data/policy_value_net.pt", device='cpu'):
    """Load trained PolicyValueNet from checkpoint, set to eval mode."""
    ckpt = torch.load(path, map_location=device, weights_only=False)
    model = PolicyValueNet(max_bullets=300).to(device)
    model.load_state_dict(ckpt['model'])
    model.eval()
    return model


# ── State encoder: live bullets → NN input tensor ──────────────────────────────

def encode_state(px, py, bullets, max_bullets=300):
    """Convert live bullet list into NN input tensors (batched, shape (1,N,5)).

    Features: [rel_x, rel_y, vx, vy, angle_norm] — all in [-1, 1].
    Returns (bullets_tensor, mask_tensor, player_tensor).
    """
    n = min(len(bullets), max_bullets)
    b_arr = np.zeros((1, max_bullets, 5), dtype=np.float32)
    m_arr = np.zeros((1, max_bullets), dtype=np.float32)
    p_arr = np.array([[px / 304.0, py / 224.0]], dtype=np.float32)

    if n > 0:
        xs = np.array([b.x for b in bullets[:n]], dtype=np.float32)
        ys = np.array([b.y for b in bullets[:n]], dtype=np.float32)
        ang = np.array([b.angle_index for b in bullets[:n]], dtype=np.int32)

        ang_idx = (ang & 63).astype(np.int32)
        vx = _VEL[ang_idx, 0]
        vy = _VEL[ang_idx, 1]

        b_arr[0, :n, 0] = (xs - px) / 304.0
        b_arr[0, :n, 1] = (ys - py) / 224.0
        b_arr[0, :n, 2] = vx
        b_arr[0, :n, 3] = vy
        b_arr[0, :n, 4] = ang.astype(np.float32) / 64.0
        m_arr[0, :n] = 1.0

    return (torch.from_numpy(b_arr), torch.from_numpy(m_arr),
            torch.from_numpy(p_arr))


# ── JIT collision check ────────────────────────────────────────────────────────

def _collision(px, py, bx, by):
    """True if bullet at (bx,by) hits player hitbox at (px,py)."""
    dx = bx - px
    dy = by - py
    return (dx >= HIT_X1 and dx < HIT_X2 and dy >= HIT_Y1 and dy < HIT_Y2)


# ── Greedy NN AI (no MCTS, just policy argmax) ─────────────────────────────────

class NNGreedyAI:
    """Direct NN policy: encode state → pick highest-probability move.

    Speed: ~1ms/frame (single forward pass). Accuracy: matches NN val acc (~72%).
    Best-case: beam-level decisions at 10× speed.
    Worst-case: no lookahead — fails when NN misreads trajectory.
    """

    def __init__(self, model_path="training_data/policy_value_net.pt"):
        self.model = load_nn_model(model_path)
        self.max_bullets = 300

    def decide(self, px, py, bullets):
        if not bullets:
            return 0
        b_t, m_t, p_t = encode_state(px, py, bullets, self.max_bullets)
        with torch.no_grad():
            policy, _ = self.model(b_t, m_t, p_t)
        best_idx = int(policy[0].argmax().item())
        return BITS[best_idx]


# ── NN-Boosted Beam Search ───────────────────────────────────────────────────

class NNBoostedBeamAI(BeamAI):
    """Beam search with NN policy preventing early pruning of escape paths.

    Core insight: beam search prunes escape paths at depth 2 because they rank
    15th by immediate danger score. Only at depth 15+ does future convergence
    reveal their value. The NN sees the escape gap from a single frame — use it
    to protect those paths through early pruning.

    Approach: run beam search TWICE per frame.
      1. Standard beam → candidate A (may be a "safe now, die later" move)
      2. NN-forced beam: lock NN's top move at depth 0 → candidate B (escape path)
    Score both candidates at intermediate checkpoints, pick the safer one.

    Speed: ~15ms/frame (2 beam searches + 1 NN forward).
    """

    NN_CONFIDENCE = 0.3

    def __init__(self, model_path="training_data/policy_value_net.pt",
                 vel_table=None, accel_table=None):
        super().__init__(vel_table=vel_table, accel_table=accel_table)
        self.nn_model = load_nn_model(model_path)
        self.max_bullets = 300
        self._overrides = 0
        self._total = 0

    def decide(self, px, py, bullets):
        if not bullets:
            return 0

        paths = self._predict(bullets)

        # ── 1. Standard beam search ──
        beam_idx = int(_beam_search(float(px), float(py), paths))

        # ── 2. NN evaluation ──
        b_t, m_t, p_t = encode_state(px, py, bullets, self.max_bullets)
        with torch.no_grad():
            nn_policy, _ = self.nn_model(b_t, m_t, p_t)
        nn_probs = F.softmax(nn_policy[0], dim=-1).numpy()
        nn_best = int(nn_probs.argmax())

        self._total += 1

        # NN agrees or not confident → trust beam
        if nn_best == beam_idx or nn_probs[nn_best] < self.NN_CONFIDENCE:
            return int(BITS[max(beam_idx, 0) % len(BITS)])

        # ── 3. Forced beam: move player to NN-chosen position, re-run beam ──
        dx = MOVES[nn_best][0] * SPEED * CHECK_EVERY
        dy = MOVES[nn_best][1] * SPEED * CHECK_EVERY
        nn_px = max(0.0, min(float(SCR_W), float(px + dx)))
        nn_py = max(0.0, min(float(SCR_H), float(py + dy)))

        # Skip the first CHECK_EVERY frames (we already moved past them)
        forced_paths = (paths[:, CHECK_EVERY:, :]
                        if paths.shape[1] > CHECK_EVERY else paths)
        nn_beam_idx = int(_beam_search(nn_px, nn_py, forced_paths))

        # ── 4. Compare: score both paths at depth 1 and 2 checkpoints ──
        beam_score = self._score_path(px, py, paths, beam_idx, beam_idx)
        nn_score   = self._score_path(px, py, paths, nn_best, nn_beam_idx)

        if nn_score < beam_score:
            self._overrides += 1
            return BITS[nn_best]
        return int(BITS[max(beam_idx, 0) % len(BITS)])

    def _score_path(self, px, py, paths, move_a, move_b):
        """Score a trajectory: move_a for CHECK_EVERY frames, then move_b."""
        score = 0.0; weight = 1.0
        px_c, py_c = px, py
        for step, move in enumerate([move_a, move_b]):
            dx = MOVES[move][0] * SPEED * CHECK_EVERY
            dy = MOVES[move][1] * SPEED * CHECK_EVERY
            px_c = max(0.0, min(float(SCR_W), px_c + dx))
            py_c = max(0.0, min(float(SCR_H), py_c + dy))
            t = (step + 1) * CHECK_EVERY
            if paths.shape[1] > t:
                d, _ = _score_pos(px_c, py_c, paths[:, t, :])
                score += d * weight
            weight *= 0.85
        return score

    @property
    def override_rate(self):
        return self._overrides / max(self._total, 1)



# ── NN Fallback over Beam Search ───────────────────────────────────────────────

class NNFallbackAI(BeamAI):
    """BeamAI with NN policy safety net.

    When beam search's result contradicts NN (NN is confident about a different
    move), use NN's choice. This catches beam search failures — typically at
    game start when bullets are sparse and beam search's 80-frame lookahead
    prunes escape paths prematurely.

    Speed: ~12ms/frame (beam search ~10ms + NN ~2ms).
    """

    NN_CONFIDENCE_THRESHOLD = 0.5  # override beam only when NN is very sure

    def __init__(self, model_path="training_data/policy_value_net.pt",
                 vel_table=None, accel_table=None):
        super().__init__(vel_table=vel_table, accel_table=accel_table)
        self.nn_model = load_nn_model(model_path)
        self.max_bullets = 300

    def decide(self, px, py, bullets):
        if not bullets:
            return 0

        # Get NN policy
        b_t, m_t, p_t = encode_state(px, py, bullets, self.max_bullets)
        with torch.no_grad():
            nn_policy, _ = self.nn_model(b_t, m_t, p_t)
        nn_probs = F.softmax(nn_policy[0], dim=-1).numpy()
        nn_best = int(nn_probs.argmax())
        nn_conf = nn_probs[nn_best]

        # Get beam search result
        beam_bits = super().decide(px, py, bullets)
        beam_idx = BITS_TO_IDX.get(beam_bits, 0)

        # Override if NN is confident AND beam disagrees
        if nn_conf >= self.NN_CONFIDENCE_THRESHOLD and nn_best != beam_idx:
            return BITS[nn_best]
        return beam_bits


# ── Smoothed Beam Search (jitter prevention) ──────────────────────────────────

class SmoothBeamAI(BeamAI):
    """Beam search with EMA-smoothed output to eliminate micro-oscillation.

    Frame-by-frame decisions have no memory, causing UP→DOWN→UP jitter when
    the "safest pixel" oscillates between two positions. This wrapper applies
    exponential moving average to the chosen direction, creating natural inertia.

    Panic bypass: if any bullet is within DANGER_RADIUS pixels, smoothing is
    disabled and the raw beam output is used directly — zero latency for dodging.

    Smoothing: 70% old momentum, 30% new direction per frame.
    """

    DANGER_RADIUS = 25  # px — bullets closer than this bypass smoothing
    SMOOTH = 0.3        # new direction weight (lower = more inertia)

    def __init__(self, vel_table=None, accel_table=None):
        super().__init__(vel_table=vel_table, accel_table=accel_table)
        self._vx = 0.0
        self._vy = 0.0

    def decide(self, px, py, bullets):
        if not bullets:
            self._vx = self._vy = 0.0
            return 0

        # Get raw beam decision
        raw_bits = super().decide(px, py, bullets)

        # Check for immediate threats — if any bullet is close, skip smoothing
        panic = False
        for b in bullets:
            if abs(b.x - px) < self.DANGER_RADIUS and abs(b.y - py) < self.DANGER_RADIUS:
                panic = True
                break

        # Map bits to (dx, dy)
        idx = _bits_to_idx(raw_bits)
        dx = MOVES[idx][0]
        dy = MOVES[idx][1]

        if panic:
            # Direct response — reset momentum to new direction
            self._vx = float(dx)
            self._vy = float(dy)
            return raw_bits

        # EMA smooth
        self._vx = (1.0 - self.SMOOTH) * self._vx + self.SMOOTH * dx
        self._vy = (1.0 - self.SMOOTH) * self._vy + self.SMOOTH * dy

        # Snap smoothed velocity to nearest discrete move
        if abs(self._vx) < 0.2 and abs(self._vy) < 0.2:
            return 0  # STOP

        best_dot, best_bits = -float('inf'), 0
        vmag = max(abs(self._vx) + abs(self._vy), 0.001)
        for mi, (mdx, mdy) in enumerate(MOVES):
            if mdx == 0 and mdy == 0:
                dot = -0.1
            else:
                mmag = (mdx * mdx + mdy * mdy) ** 0.5
                dot = (mdx * self._vx + mdy * self._vy) / (mmag * vmag)
            if dot > best_dot:
                best_dot, best_bits = dot, BITS[mi]

        return best_bits


def _bits_to_idx(bits):
    for i, b in enumerate(BITS):
        if b == bits:
            return i
    return 0

if __name__ == "__main__":
    # Quick smoke test with simulated bullets
    class FakeBullet:
        def __init__(self, x, y, angle):
            self.x = x; self.y = y; self.angle_index = angle

    fake_bullets = [FakeBullet(152 + i*5, 112 + i*3, i) for i in range(30)]

    for name, cls in [("Greedy", NNGreedyAI), ("MCTS", NNMCTSAI),
                       ("Fallback", NNFallbackAI)]:
        try:
            if cls == NNFallbackAI:
                ai = cls()
            else:
                ai = cls()
            move = ai.decide(152, 112, fake_bullets)
            print(f"{name}: px=152 py=112 → BITS={move} ({BITS_TO_IDX.get(move, '?')})")
        except FileNotFoundError:
            print(f"{name}: model not found (train first)")
