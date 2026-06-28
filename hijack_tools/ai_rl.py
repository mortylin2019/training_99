"""
ai_rl.py — DQN (Deep Q-Network) agent for Training 99.

Learns to dodge bullets through reinforcement learning in the simulator.
Same interface as ai_beam.py: decide(px, py, bullets) → bits

Features: finer state grid, nearest-bullet coords, checkpoint save/resume, tqdm.
"""
import numpy as np
import torch
import torch.nn as nn
import random
import os
from collections import deque
from loguru import logger

# ── State encoding (CNN grid + temporal) ────────────────────
GRID_W, GRID_H = 32, 24
N_CHANNELS = 4                # density, prev_density, player, walls

SCR_W, SCR_H = 304, 224
CTR_X, CTR_Y = 152, 44

MOVES = np.array([
    [ 0,  0], [-1,  0], [ 1,  0], [ 0, -1], [ 0,  1],
    [-1, -1], [-1,  1], [ 1, -1], [ 1,  1],
], dtype=np.int32)
BITS = np.array([0, 1, 8, 2, 4, 3, 5, 10, 12], dtype=np.int32)
N_ACTIONS = 9


def encode_state(px, py, bullets, graze=0, frame=0, prev_density=None):
    """
    CNN grid state: 4 channels.
    Channel 0: bullet density (current frame)
    Channel 1: previous frame density (CNN learns motion from 0 vs 1)
    Channel 2: player position (Gaussian blob)
    Channel 3: wall proximity mask
    """
    grid = np.zeros((N_CHANNELS, GRID_H, GRID_W), dtype=np.float32)
    cell_w = SCR_W / GRID_W
    cell_h = SCR_H / GRID_H
    counts = np.zeros((GRID_H, GRID_W), dtype=np.float32)

    for b in bullets:
        if b.angle_index == 0xFF:
            continue
        gx = min(int(b.x / cell_w), GRID_W - 1)
        gy = min(int(b.y / cell_h), GRID_H - 1)
        if 0 <= gx < GRID_W and 0 <= gy < GRID_H:
            counts[gy, gx] += 1.0

    # Channel 0: current density
    grid[0] = np.clip(counts / 5.0, 0.0, 1.0)

    # Channel 1: previous density (motion cue)
    if prev_density is not None:
        grid[1] = prev_density

    # Channel 2: player position (Gaussian blob)
    px_cell = px / cell_w
    py_cell = py / cell_h
    for gy in range(GRID_H):
        for gx in range(GRID_W):
            dist2 = (gx - px_cell) ** 2 + (gy - py_cell) ** 2
            grid[2, gy, gx] = np.exp(-dist2 / 2.0)

    # Channel 3: wall proximity (1.0 at edges, 0.0 center)
    for gy in range(GRID_H):
        for gx in range(GRID_W):
            dx = min(gx, GRID_W - 1 - gx) / max(GRID_W * 0.15, 1)
            dy = min(gy, GRID_H - 1 - gy) / max(GRID_H * 0.15, 1)
            grid[3, gy, gx] = 1.0 - min(dx, dy, 1.0)

    return grid


class QNetwork(nn.Module):
    """Light CNN: 32×24 → 2 convs → pool → 768 → 128 → 9."""
    def __init__(self, n_actions=N_ACTIONS):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(N_CHANNELS, 16, 3, padding=1), nn.ReLU(),
            nn.Conv2d(16, 16, 3, padding=1, stride=2), nn.ReLU(),  # 16×12
        )
        self.pool = nn.AdaptiveAvgPool2d((6, 8))  # → 16×6×8 = 768
        self.head = nn.Sequential(
            nn.Linear(768, 128), nn.ReLU(),
            nn.Linear(128, n_actions),
        )

    def forward(self, x):
        f = self.conv(x)
        f = self.pool(f)
        return self.head(f.view(f.size(0), -1))


class RLAgent:
    """DQN with CNN, experience replay, target network, save/resume."""

    def __init__(self, n_actions=N_ACTIONS,
                 lr=1e-3, gamma=0.99, epsilon=1.0, epsilon_min=0.02,
                 epsilon_decay=0.997, buffer_size=50000, batch_size=128,
                 target_update=500):
        self.n_actions = n_actions
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        self.target_update = target_update

        self.q_net = QNetwork(n_actions)
        self.target_net = QNetwork(n_actions)
        self.target_net.load_state_dict(self.q_net.state_dict())
        self.optimizer = torch.optim.Adam(self.q_net.parameters(), lr=lr)
        self.loss_fn = nn.SmoothL1Loss()

        self.replay = deque(maxlen=buffer_size)
        self.train_steps = 0
        self.episodes = 0

    def decide(self, px, py, bullets, graze=0, frame=0):
        """Epsilon-greedy over CNN Q-values. Returns bitmask int."""
        prev = getattr(self, '_prev_density', None)
        state = encode_state(px, py, bullets, graze, frame, prev)
        self._prev_density = state[0].copy()  # store density for next frame
        if random.random() < self.epsilon:
            return int(BITS[random.randint(0, N_ACTIONS - 1)])
        with torch.no_grad():
            s = torch.from_numpy(state).unsqueeze(0)  # (1, C, H, W)
            action = self.q_net(s).argmax(dim=1).item()
        return int(BITS[action])

    def remember(self, state, action_idx, reward, next_state, done):
        self.replay.append((state, action_idx, reward, next_state, done))

    def train_step(self):
        if len(self.replay) < self.batch_size:
            return None
        batch = random.sample(self.replay, self.batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        states = torch.from_numpy(np.stack(states))
        actions = torch.tensor(actions, dtype=torch.long).unsqueeze(1)
        rewards = torch.tensor(rewards, dtype=torch.float32).unsqueeze(1)
        next_states = torch.from_numpy(np.stack(next_states))
        dones = torch.tensor(dones, dtype=torch.float32).unsqueeze(1)

        q_current = self.q_net(states).gather(1, actions)
        with torch.no_grad():
            q_next = self.target_net(next_states).max(dim=1, keepdim=True)[0]
            q_target = rewards + self.gamma * q_next * (1 - dones)

        loss = self.loss_fn(q_current, q_target)
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.q_net.parameters(), 10.0)
        self.optimizer.step()

        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        self.train_steps += 1
        if self.train_steps % self.target_update == 0:
            self.target_net.load_state_dict(self.q_net.state_dict())
        return loss.item()

    def end_episode(self):
        self.episodes += 1

    def save(self, path):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        torch.save({
            'q_net': self.q_net.state_dict(),
            'target_net': self.target_net.state_dict(),
            'optimizer': self.optimizer.state_dict(),
            'epsilon': self.epsilon,
            'episodes': self.episodes,
            'train_steps': self.train_steps,
        }, path)

    def load(self, path):
        if not os.path.exists(path):
            return False
        ckpt = torch.load(path, weights_only=False)
        self.q_net.load_state_dict(ckpt['q_net'])
        self.target_net.load_state_dict(ckpt['target_net'])
        if 'optimizer' in ckpt:
            self.optimizer.load_state_dict(ckpt['optimizer'])
        self.epsilon = ckpt.get('epsilon', self.epsilon)
        self.episodes = ckpt.get('episodes', 0)
        self.train_steps = ckpt.get('train_steps', 0)
        return True

    def export_for_c(self, path):
        """Export for C inference (not yet supported for CNN — returns None)."""
        return None  # C inference engine doesn't support CNN yet


# ── Collection worker (PyTorch CNN, runs in subprocess) ─────
def _collect_worker(args):
    """Run N episodes with PyTorch CNN, return (transitions, ep_frames)."""
    model_state, epsilon, n_eps, difficulty, max_frames, seed_base = args

    agent = RLAgent()
    agent.q_net.load_state_dict(model_state)
    agent.epsilon = epsilon

    try:
        from hijack_tools.simulator.c_wrapper import CSimulator
    except ImportError:
        from simulator.c_wrapper import CSimulator

    transitions = []
    ep_frames = []
    for ep in range(n_eps):
        cs = CSimulator(difficulty, seed_base + ep)
        state = encode_state(cs.px, cs.py, cs.get_visible_bullets())
        frames = 0
        for f in range(max_frames):
            if random.random() < epsilon:
                action_idx = random.randint(0, N_ACTIONS - 1)
            else:
                with torch.no_grad():
                    s = torch.from_numpy(state).unsqueeze(0)
                    action_idx = agent.q_net(s).argmax(dim=1).item()

            bits = int(BITS[action_idx])
            alive, bullets = cs.step(bits)
            next_state = encode_state(cs.px, cs.py, bullets)

            reward = 0.02
            if not alive:
                reward = -2.0 + f * 0.0005

            transitions.append((state, action_idx, reward, next_state, not alive))
            state = next_state
            frames = f + 1
            if not alive:
                break
        ep_frames.append(frames)
    return transitions, ep_frames


# ── Parallel batch training loop (C inference) ──────────────
def train(episodes=10000, difficulty=1, max_frames=8000,
          workers=8, collect_eps=64, train_epochs=5,
          save_path="logs/ai_rl_model.pt", resume=True):
    """
    Parallel collect-then-train DQN with C inference:
      1. Export PyTorch weights → .bin
      2. Workers collect episodes using pure C inference (56× faster)
      3. Train on combined replay buffer in PyTorch
      4. Repeat
    """
    from concurrent.futures import ProcessPoolExecutor

    agent = RLAgent()
    start_ep = 0

    if resume and os.path.exists(save_path):
        if agent.load(save_path):
            start_ep = agent.episodes
            logger.info(f"Resumed from {save_path} (ep {start_ep}, eps={agent.epsilon:.3f})")

    history = []
    ep = start_ep
    while ep < episodes:
        # ── Phase 1: Collect with Python workers (parallel) ─
        n_collect = min(collect_eps, episodes - ep)
        per_worker = max(1, n_collect // workers)
        actual_workers = min(workers, n_collect)

        args_list = []
        for w in range(actual_workers):
            n = per_worker + (1 if w < n_collect % actual_workers else 0)
            if n > 0:
                args_list.append((
                    agent.q_net.state_dict(), agent.epsilon,
                    n, difficulty, max_frames,
                    (ep + w * per_worker) * 12345 + 789
                ))

        all_transitions = []
        all_ep_frames = []
        with ProcessPoolExecutor(max_workers=actual_workers) as pool:
            futures = [pool.submit(_collect_worker, a) for a in args_list]
            for future in futures:
                try:
                    trans, ep_frames = future.result()
                    all_transitions.extend(trans)
                    all_ep_frames.extend(ep_frames)
                except Exception as e:
                    logger.warning(f"Worker failed: {e}")

        for t in all_transitions:
            agent.remember(*t)
        for f in all_ep_frames:
            history.append(f / 80.0)

        ep += n_collect

        # ── Phase 2: Train in PyTorch ───────────────────────
        train_losses = []
        for epoch in range(train_epochs):
            epoch_loss = 0.0
            n_batches = 0
            buf = list(agent.replay)
            random.shuffle(buf)
            for i in range(0, len(buf), agent.batch_size):
                batch = buf[i:i + agent.batch_size]
                if len(batch) < agent.batch_size:
                    break
                states, actions, rewards, next_states, dones = zip(*batch)
                states = torch.from_numpy(np.array(states, dtype=np.float32))
                actions = torch.tensor(actions, dtype=torch.long).unsqueeze(1)
                rewards = torch.tensor(rewards, dtype=torch.float32).unsqueeze(1)
                next_states = torch.from_numpy(np.array(next_states, dtype=np.float32))
                dones = torch.tensor(dones, dtype=torch.float32).unsqueeze(1)

                q_current = agent.q_net(states).gather(1, actions)
                with torch.no_grad():
                    q_next = agent.target_net(next_states).max(dim=1, keepdim=True)[0]
                    q_target = rewards + agent.gamma * q_next * (1 - dones)

                loss = agent.loss_fn(q_current, q_target)
                agent.optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(agent.q_net.parameters(), 10.0)
                agent.optimizer.step()

                epoch_loss += loss.item()
                n_batches += 1
                agent.train_steps += 1

            if n_batches > 0:
                train_losses.append(epoch_loss / n_batches)

        agent.epsilon = max(agent.epsilon_min, agent.epsilon * (agent.epsilon_decay ** n_collect))
        if agent.train_steps % agent.target_update < n_collect:
            agent.target_net.load_state_dict(agent.q_net.state_dict())

        # ── Progress ────────────────────────────────────────
        avg_loss = sum(train_losses) / max(len(train_losses), 1) if train_losses else 0
        recent = history[-100:] if len(history) >= 100 else history
        avg_surv = sum(recent) / max(len(recent), 1) if recent else 0

        if len(history) > 0:
            agent.episodes = ep
            agent.save(save_path)
            logger.info(
                f"ep {ep:>5}/{episodes} | surv={avg_surv:.1f}s "
                f"eps={agent.epsilon:.2f} loss={avg_loss:.4f} "
                f"buf={len(agent.replay)} | saved")

    return agent, history


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Parallel DQN RL Agent for Training 99")
    p.add_argument("--episodes", type=int, default=10000, help="Total training episodes")
    p.add_argument("--difficulty", type=int, default=1)
    p.add_argument("--max-frames", type=int, default=8000)
    p.add_argument("--workers", type=int, default=8, help="Parallel workers for collection")
    p.add_argument("--collect-eps", type=int, default=64, help="Episodes per collection round")
    p.add_argument("--train-epochs", type=int, default=5, help="Training epochs per round")
    p.add_argument("--save", default="logs/ai_rl_model.pt")
    p.add_argument("--no-resume", action="store_true")
    args = p.parse_args()
    agent, history = train(
        episodes=args.episodes, difficulty=args.difficulty,
        max_frames=args.max_frames, workers=args.workers,
        collect_eps=args.collect_eps, train_epochs=args.train_epochs,
        save_path=args.save, resume=not args.no_resume)
    tail = min(100, len(history))
    if tail > 0:
        print(f"\nFinal {tail}-ep avg: {sum(history[-tail:])/len(history[-tail:]):.1f}s")
        print(f"Best ep: {max(history):.1f}s  Worst: {min(history):.1f}s")
