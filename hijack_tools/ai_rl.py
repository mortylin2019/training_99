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

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

# ── State encoding ──────────────────────────────────────────
MAX_BULLETS = 100              # pad to fixed size
BULLET_FEATS = 4               # (x, y, vx, vy) per bullet
STATE_DIM = MAX_BULLETS * BULLET_FEATS + 4  # bullets + player(x,y) + graze + frame_norm

SCR_W, SCR_H = 304, 224
CTR_X, CTR_Y = 152, 44

MOVES = np.array([
    [ 0,  0], [-1,  0], [ 1,  0], [ 0, -1], [ 0,  1],
    [-1, -1], [-1,  1], [ 1, -1], [ 1,  1],
], dtype=np.int32)
BITS = np.array([0, 1, 8, 2, 4, 3, 5, 10, 12], dtype=np.int32)
N_ACTIONS = 9

try:
    from hijack_tools.simulator.tables import VEL_TABLE, ACCEL_TABLE
except ImportError:
    from simulator.tables import VEL_TABLE, ACCEL_TABLE


def encode_state(px, py, bullets, graze=0, frame=0):
    """Flat state: all bullets (x,y,vx,vy) padded + player + graze + time."""
    state = np.zeros(STATE_DIM, dtype=np.float32)
    n = 0
    for b in bullets:
        if b.angle_index == 0xFF or n >= MAX_BULLETS:
            continue
        bx, by = b.x, b.y
        # Velocity (fair: visible from frame-to-frame movement)
        if b.type == 2:
            vx, vy = b.vx, b.vy
        elif b.type == 3:
            vx, vy = ACCEL_TABLE[b.angle_index & 63]
        else:
            vx, vy = VEL_TABLE[b.angle_index & 63]
        off = n * BULLET_FEATS
        state[off] = bx / SCR_W
        state[off + 1] = by / SCR_H
        state[off + 2] = vx / 8.0       # velocity normalized to ~[-10,10]
        state[off + 3] = vy / 8.0
        n += 1

    # Player info at the end (fixed position regardless of bullet count)
    base = MAX_BULLETS * BULLET_FEATS
    state[base] = px / SCR_W
    state[base + 1] = py / SCR_H
    state[base + 2] = min(graze / 50.0, 1.0)   # graze count (capped)
    state[base + 3] = min(frame / 8000.0, 1.0)  # time progress
    return state


class QNetwork(nn.Module):
    """MLP: state → Q-values for 9 actions."""
    def __init__(self, state_dim=STATE_DIM, n_actions=N_ACTIONS, hidden=256):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden // 2),
            nn.ReLU(),
            nn.Linear(hidden // 2, n_actions),
        )

    def forward(self, x):
        return self.net(x)


class RLAgent:
    """DQN with experience replay, target network, save/resume."""

    def __init__(self, state_dim=STATE_DIM, n_actions=N_ACTIONS,
                 lr=1e-3, gamma=0.99, epsilon=1.0, epsilon_min=0.02,
                 epsilon_decay=0.997, buffer_size=50000, batch_size=128,
                 target_update=500):
        self.state_dim = state_dim
        self.n_actions = n_actions
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        self.target_update = target_update

        self.q_net = QNetwork(state_dim, n_actions)
        self.target_net = QNetwork(state_dim, n_actions)
        self.target_net.load_state_dict(self.q_net.state_dict())
        self.optimizer = torch.optim.Adam(self.q_net.parameters(), lr=lr)
        self.loss_fn = nn.SmoothL1Loss()  # Huber loss — more stable

        self.replay = deque(maxlen=buffer_size)
        self.train_steps = 0
        self.episodes = 0

    def decide(self, px, py, bullets, graze=0, frame=0):
        """Epsilon-greedy action selection. Returns bitmask int."""
        state = encode_state(px, py, bullets, graze, frame)
        if random.random() < self.epsilon:
            return int(BITS[random.randint(0, N_ACTIONS - 1)])
        with torch.no_grad():
            s = torch.from_numpy(state).unsqueeze(0)
            action = self.q_net(s).argmax(dim=1).item()
        return int(BITS[action])

    def remember(self, state, action_idx, reward, next_state, done):
        self.replay.append((state, action_idx, reward, next_state, done))

    def train_step(self):
        if len(self.replay) < self.batch_size:
            return None
        batch = random.sample(self.replay, self.batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        states = torch.from_numpy(np.array(states, dtype=np.float32))
        actions = torch.tensor(actions, dtype=torch.long).unsqueeze(1)
        rewards = torch.tensor(rewards, dtype=torch.float32).unsqueeze(1)
        next_states = torch.from_numpy(np.array(next_states, dtype=np.float32))
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


# ── Parallel collection worker (runs in subprocess) ─────────
def _collect_worker(args):
    """Run N episodes, return (transitions, episode_frames_list). Picklable."""
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


# ── Parallel batch training loop ────────────────────────────
def train(episodes=10000, difficulty=1, max_frames=8000,
          workers=8, collect_eps=64, train_epochs=5,
          save_path="logs/ai_rl_model.pt", resume=True):
    """
    Parallel collect-then-train DQN:
      1. Spawn `workers` processes, each runs `collect_eps/workers` episodes
      2. Gather all (s,a,r,s',done) transitions into replay buffer
      3. Train on combined buffer for `train_epochs` epochs
      4. Repeat until `episodes` total

    Uses C engine for 7× faster simulation per episode.
    """
    from concurrent.futures import ProcessPoolExecutor
    import math

    agent = RLAgent()
    start_ep = 0

    if resume and os.path.exists(save_path):
        if agent.load(save_path):
            start_ep = agent.episodes
            print(f"Resumed from {save_path} (ep {start_ep}, eps={agent.epsilon:.3f})")

    history = []
    pbar = tqdm(total=episodes, initial=start_ep, desc="Training",
                unit="ep", disable=not HAS_TQDM,
                bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}] {postfix}')

    ep = start_ep
    while ep < episodes:
        # ── Phase 1: Collect experience in parallel ──────────
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
                    print(f"Worker failed: {e}")

        # Add to replay buffer and track survival
        for t in all_transitions:
            agent.remember(*t)
        for f in all_ep_frames:
            history.append(f / 80.0)  # frames → seconds

        ep += n_collect
        total_frames_collected = sum(1 for t in all_transitions)

        # ── Phase 2: Train on collected data ────────────────
        train_losses = []
        for epoch in range(train_epochs):
            epoch_loss = 0.0
            n_batches = 0
            # Shuffle and batch
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

        # Decay epsilon
        agent.epsilon = max(agent.epsilon_min, agent.epsilon * (agent.epsilon_decay ** n_collect))

        # Update target network
        if agent.train_steps % agent.target_update < n_collect:
            agent.target_net.load_state_dict(agent.q_net.state_dict())

        # ── Progress ────────────────────────────────────────
        avg_loss = sum(train_losses) / max(len(train_losses), 1) if train_losses else 0
        recent = history[-100:] if len(history) >= 100 else history
        avg_surv = sum(recent) / max(len(recent), 1) if recent else 0
        pbar.update(n_collect)
        pbar.set_postfix({
            'surv': f'{avg_surv:.1f}s', 'eps': f'{agent.epsilon:.3f}',
            'buf': len(agent.replay), 'loss': f'{avg_loss:.4f}',
        })

        # Save checkpoint
        if len(history) > 0:
            agent.episodes = ep
            agent.save(save_path)
            if avg_surv > 0:
                pbar.write(f"  saved @ ep {ep} (avg {avg_surv:.1f}s, loss={avg_loss:.4f})")

    pbar.close()
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
