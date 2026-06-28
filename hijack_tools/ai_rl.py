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
GRID_W, GRID_H = 24, 18       # finer grid (~12.7×12.4 px per cell)
N_NEAREST = 10                # closest bullet coords to include
STATE_DIM = GRID_W * GRID_H + N_NEAREST * 2 + 2  # grid + nearest bullets + player

SCR_W, SCR_H = 304, 224
CTR_X, CTR_Y = 152, 44

MOVES = np.array([
    [ 0,  0], [-1,  0], [ 1,  0], [ 0, -1], [ 0,  1],
    [-1, -1], [-1,  1], [ 1, -1], [ 1,  1],
], dtype=np.int32)
BITS = np.array([0, 1, 8, 2, 4, 3, 5, 10, 12], dtype=np.int32)
N_ACTIONS = 9


def encode_state(px, py, bullets):
    """Rich state: density grid + nearest bullet coords + player position."""
    grid = np.zeros((GRID_H, GRID_W), dtype=np.float32)
    cell_w = SCR_W / GRID_W
    cell_h = SCR_H / GRID_H
    active = [(b.x, b.y) for b in bullets if b.angle_index != 0xFF]
    coords = []
    for bx, by in active:
        gx = min(int(bx / cell_w), GRID_W - 1)
        gy = min(int(by / cell_h), GRID_H - 1)
        if 0 <= gx < GRID_W and 0 <= gy < GRID_H:
            grid[gy, gx] += 1.0
        coords.append((bx, by))
    grid = np.clip(grid / 5.0, 0.0, 1.0)
    if coords:
        coords.sort(key=lambda c: (c[0]-px)**2 + (c[1]-py)**2)
        nearest = coords[:N_NEAREST]
    else:
        nearest = []
    while len(nearest) < N_NEAREST:
        nearest.append((0, 0))
    nearest_flat = []
    for bx, by in nearest:
        nearest_flat.extend([bx / SCR_W, by / SCR_H])
    state = np.concatenate([
        grid.flatten(),
        np.array(nearest_flat, dtype=np.float32),
        np.array([px / SCR_W, py / SCR_H], dtype=np.float32)
    ])
    return state.astype(np.float32)


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

    def decide(self, px, py, bullets):
        """Epsilon-greedy action selection. Returns bitmask int."""
        state = encode_state(px, py, bullets)
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


# ── Training loop ───────────────────────────────────────────
def train(episodes=1000, difficulty=1, max_frames=8000,
          render_every=100, save_path="logs/ai_rl_model.pt",
          resume=True):
    """Train DQN with tqdm progress bar, checkpoint resume."""
    try:
        from hijack_tools.simulator.engine import GameSimulator
    except ImportError:
        from simulator.engine import GameSimulator

    agent = RLAgent()
    start_ep = 0

    if resume and os.path.exists(save_path):
        if agent.load(save_path):
            start_ep = agent.episodes
            print(f"Resumed from {save_path} (ep {start_ep}, eps={agent.epsilon:.3f})")

    sim = GameSimulator(difficulty=difficulty, seed=42)
    history = []
    best_avg = 0.0
    recent_survivals = deque(maxlen=render_every)

    pbar = tqdm(range(start_ep + 1, episodes + 1), desc="Training",
                unit="ep", disable=not HAS_TQDM,
                bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}] {postfix}')

    for ep in pbar:
        sim.reset()
        sim.rng.seed(ep * 12345 + 789)
        state = encode_state(sim.px, sim.py, sim.get_visible_bullets())
        steps = 0
        ep_loss = 0.0
        total_reward = 0.0

        for _ in range(max_frames):
            if random.random() < agent.epsilon:
                action_idx = random.randint(0, N_ACTIONS - 1)
            else:
                with torch.no_grad():
                    s = torch.from_numpy(state).unsqueeze(0)
                    action_idx = agent.q_net(s).argmax(dim=1).item()

            bits = int(BITS[action_idx])
            alive, bullets = sim.step(bits)
            next_state = encode_state(sim.px, sim.py, bullets)

            reward = 0.02
            if sim.active_near > 0:
                reward += 0.002 * sim.active_near
            if not alive:
                reward = -2.0 + steps * 0.0005

            total_reward += reward
            steps += 1

            agent.remember(state, action_idx, reward, next_state, not alive)
            loss = agent.train_step()
            if loss is not None:
                ep_loss += loss

            state = next_state
            if not alive:
                break

        agent.end_episode()
        survival = steps / 80.0
        history.append(survival)
        recent_survivals.append(survival)

        if ep % 10 == 0:
            avg_rec = sum(recent_survivals) / max(len(recent_survivals), 1)
            pbar.set_postfix({
                'surv': f'{avg_rec:.1f}s', 'eps': f'{agent.epsilon:.3f}',
                'buf': len(agent.replay), 'R': f'{total_reward:.1f}',
            })

        if ep % render_every == 0:
            avg_rec = sum(recent_survivals) / max(len(recent_survivals), 1)
            if avg_rec >= best_avg:
                best_avg = avg_rec
                agent.save(save_path)
                pbar.write(f"  saved @ ep {ep} (avg {avg_rec:.1f}s)")

    pbar.close()
    return agent, history


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="DQN RL Agent for Training 99")
    p.add_argument("--episodes", type=int, default=1000)
    p.add_argument("--difficulty", type=int, default=1)
    p.add_argument("--max-frames", type=int, default=8000)
    p.add_argument("--render-every", type=int, default=100)
    p.add_argument("--save", default="logs/ai_rl_model.pt")
    p.add_argument("--no-resume", action="store_true")
    args = p.parse_args()
    agent, history = train(
        episodes=args.episodes, difficulty=args.difficulty,
        max_frames=args.max_frames, render_every=args.render_every,
        save_path=args.save, resume=not args.no_resume)
    tail = min(100, len(history))
    print(f"\nFinal {tail}-ep avg: {sum(history[-tail:])/len(history[-tail:]):.1f}s")
    print(f"Best ep: {max(history):.1f}s  Worst: {min(history):.1f}s")
