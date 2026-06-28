"""
ai_rl.py — DQN (Deep Q-Network) agent for Training 99.

Learns to dodge bullets through reinforcement learning in the simulator.
Uses a grid-based state representation: divides screen into cells, counts
bullets per cell, adds player position. Trained via DQN with experience replay.

Same interface as ai_beam.py: decide(px, py, bullets) → bits
"""
import numpy as np
import torch
import torch.nn as nn
import random
from collections import deque

# ── State encoding ──────────────────────────────────────────
GRID_W, GRID_H = 16, 12
STATE_DIM = GRID_W * GRID_H + 2

SCR_W, SCR_H = 304, 224
CTR_X, CTR_Y = 152, 44

MOVES = np.array([
    [ 0,  0], [-1,  0], [ 1,  0], [ 0, -1], [ 0,  1],
    [-1, -1], [-1,  1], [ 1, -1], [ 1,  1],
], dtype=np.int32)
BITS = np.array([0, 1, 8, 2, 4, 3, 5, 10, 12], dtype=np.int32)
N_ACTIONS = 9


def encode_state(px, py, bullets):
    """Encode game state into a fixed-size vector for the neural network."""
    grid = np.zeros((GRID_H, GRID_W), dtype=np.float32)
    cell_w = SCR_W / GRID_W
    cell_h = SCR_H / GRID_H
    for b in bullets:
        if b.angle_index == 0xFF:
            continue
        gx = min(int(b.x / cell_w), GRID_W - 1)
        gy = min(int(b.y / cell_h), GRID_H - 1)
        if 0 <= gx < GRID_W and 0 <= gy < GRID_H:
            grid[gy, gx] += 1.0
    grid = np.clip(grid / 5.0, 0.0, 1.0)
    state = np.concatenate([
        grid.flatten(),
        np.array([px / SCR_W, py / SCR_H], dtype=np.float32)
    ])
    return state.astype(np.float32)


class QNetwork(nn.Module):
    """Small MLP: state → Q-values for 9 actions."""
    def __init__(self, state_dim=STATE_DIM, n_actions=N_ACTIONS, hidden=128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden // 2),
            nn.ReLU(),
            nn.Linear(hidden // 2, n_actions),
        )

    def forward(self, x):
        return self.net(x)


class RLAgent:
    """
    DQN agent with experience replay and target network.
    Same decide() interface as ai_beam.py and ai_direct.py.
    Call train_step() after each episode to learn.
    """

    def __init__(self, state_dim=STATE_DIM, n_actions=N_ACTIONS,
                 lr=1e-3, gamma=0.99, epsilon=1.0, epsilon_min=0.05,
                 epsilon_decay=0.995, buffer_size=10000, batch_size=64,
                 target_update=200):
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
        self.loss_fn = nn.MSELoss()

        self.replay = deque(maxlen=buffer_size)
        self.train_steps = 0
        self.episodes = 0

    def decide(self, px, py, bullets):
        """Pick action: epsilon-greedy over Q-values. Returns bitmask int."""
        state = encode_state(px, py, bullets)
        if random.random() < self.epsilon:
            return int(BITS[random.randint(0, N_ACTIONS - 1)])
        with torch.no_grad():
            s = torch.from_numpy(state).unsqueeze(0)
            q = self.q_net(s)
            action = q.argmax(dim=1).item()
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
        self.optimizer.step()
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        self.train_steps += 1
        if self.train_steps % self.target_update == 0:
            self.target_net.load_state_dict(self.q_net.state_dict())
        return loss.item()

    def end_episode(self):
        self.episodes += 1

    def save(self, path):
        torch.save({
            'q_net': self.q_net.state_dict(),
            'epsilon': self.epsilon,
            'episodes': self.episodes,
            'train_steps': self.train_steps,
        }, path)

    def load(self, path):
        ckpt = torch.load(path)
        self.q_net.load_state_dict(ckpt['q_net'])
        self.target_net.load_state_dict(ckpt['q_net'])
        self.epsilon = ckpt.get('epsilon', self.epsilon)
        self.episodes = ckpt.get('episodes', 0)
        self.train_steps = ckpt.get('train_steps', 0)


# ── Training loop ───────────────────────────────────────────
def train(episodes=500, difficulty=1, max_frames=8000,
          render_every=50, save_path="logs/ai_rl_model.pt"):
    """Train DQN agent in the simulator. Prints progress every N episodes."""
    try:
        from hijack_tools.simulator.engine import GameSimulator
    except ImportError:
        from simulator.engine import GameSimulator

    agent = RLAgent()
    sim = GameSimulator(difficulty=difficulty, seed=42)

    history = []
    best_avg = 0.0

    for ep in range(1, episodes + 1):
        sim.reset()
        sim.rng.seed(ep * 12345)
        state = encode_state(sim.px, sim.py, sim.get_visible_bullets())
        total_reward = 0.0
        ep_loss = 0.0
        steps = 0

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

            reward = 0.01
            if sim.active_near > 0:
                reward += 0.001 * sim.active_near
            if not alive:
                reward = -1.0 + steps * 0.0001

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

        if ep % render_every == 0:
            recent = history[-render_every:]
            avg_s = sum(recent) / len(recent)
            best_s = max(recent)
            print(f"Ep {ep:>4}: eps={agent.epsilon:.3f}  "
                  f"surv={avg_s:.1f}s (best {best_s:.1f}s)  "
                  f"loss={ep_loss/max(steps,1):.4f}  buf={len(agent.replay)}")
            if avg_s > best_avg:
                best_avg = avg_s
                agent.save(save_path)
                print(f"  -> saved (avg {avg_s:.1f}s)")

    return agent, history


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="DQN RL Agent for Training 99")
    p.add_argument("--episodes", type=int, default=200)
    p.add_argument("--difficulty", type=int, default=1)
    p.add_argument("--max-frames", type=int, default=8000)
    p.add_argument("--render-every", type=int, default=50)
    p.add_argument("--save", default="logs/ai_rl_model.pt")
    args = p.parse_args()
    agent, history = train(episodes=args.episodes, difficulty=args.difficulty,
                           max_frames=args.max_frames, render_every=args.render_every,
                           save_path=args.save)
    tail = min(50, len(history))
    print(f"\nFinal {tail}-ep avg: {sum(history[-tail:])/len(history[-tail:]):.1f}s")
