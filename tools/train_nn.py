#!/usr/bin/env python3
"""Train a DeepSet policy+value NN on beam search data. Resumable.

Key design decisions (2026-07-04 audit):
  - Relative bullet positions (bx-px, by-py) → translation-invariant danger patterns
  - BatchNorm in trunk → stable training with mixed-scale features
  - Cosine annealing LR → fast convergence without manual tuning
  - 80/20 validation split + early stopping → prevent overfitting on large datasets
  - Gradient clipping at 1.0 → guard against spike instability

Input: combined .npz (from `gen_training_data.py --combine`)
Usage:
  python3 tools/train_nn.py --data training_data/combined.npz --epochs 100
  python3 tools/train_nn.py --resume training_data/policy_value_net.pt
"""
import sys, os, argparse
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader, random_split
from torch.optim.lr_scheduler import CosineAnnealingLR
from tqdm import tqdm

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from hijack_tools.simulator.tables import VEL_TABLE

BITS = [0, 1, 8, 2, 4, 3, 5, 10, 12]
BITS_TO_IDX = {b: i for i, b in enumerate(BITS)}
IDX_TO_BITS = {i: b for i, b in enumerate(BITS)}

_VEL = np.array([(VEL_TABLE[i][0] / 64.0, VEL_TABLE[i][1] / 64.0)
                 for i in range(64)], dtype=np.float32)


class DeepSet(nn.Module):
    """Encode variable-size bullet set → fixed vector via attention-weighted pooling.

    A learned scalar scorer rates each bullet's importance; softmax over active
    bullets produces attention weights. Cost: O(N·d), same as mean pooling.
    When all mask entries are zero (no bullets), returns zero vector.
    """

    def __init__(self, bullet_dim=5, hidden=128, out_dim=64):
        super().__init__()
        self.bullet_enc = nn.Sequential(
            nn.Linear(bullet_dim, hidden), nn.ReLU(),
            nn.Linear(hidden, hidden), nn.ReLU(),
            nn.Linear(hidden, out_dim),
        )
        self.scorer = nn.Linear(out_dim, 1)  # +64 params — negligible

    def forward(self, bullets, mask):
        B, N, _ = bullets.shape
        x = self.bullet_enc(bullets.view(B * N, -1)).view(B, N, -1)

        # Attention scalar per bullet — learn what makes a bullet "dangerous"
        scores = self.scorer(x).squeeze(-1)  # (B, N)
        mask_bool = mask.bool()
        scores = scores.masked_fill(~mask_bool, float('-inf'))
        weights = F.softmax(scores, dim=1)
        # Samples with zero active bullets → softmax(NaN) → replace with zeros
        weights = torch.where(weights.isnan(), torch.zeros_like(weights), weights)

        x = x * weights.unsqueeze(-1)
        return x.sum(dim=1)


class PolicyValueNet(nn.Module):
    """DeepSet encoder + player state → policy head (9 moves) + value head."""

    def __init__(self, max_bullets=300, bullet_dim=5, player_dim=2):
        super().__init__()
        self.deepset = DeepSet(bullet_dim=bullet_dim)
        self.trunk = nn.Sequential(
            nn.Linear(64 + player_dim, 256), nn.BatchNorm1d(256), nn.ReLU(),
            nn.Linear(256, 128),      nn.BatchNorm1d(128), nn.ReLU(),
        )
        self.policy_head = nn.Linear(128, 9)
        self.value_head = nn.Linear(128, 1)

    def forward(self, bullets, mask, player):
        enc = self.deepset(bullets, mask)
        x = torch.cat([enc, player], dim=1)
        x = self.trunk(x)
        return self.policy_head(x), self.value_head(x).squeeze(-1)


class BulletDataset(Dataset):
    """Load from combined .npz — relative bullet coordinates + velocity lookup.

    Bullet features (player-centric, 5-dim, all in [-1, 1]):
      [0] (bx - px) / 304.0   — relative x, translation-invariant
      [1] (by - py) / 224.0   — relative y
      [2] vx                   — velocity in [-1, 1] from VEL_TABLE
      [3] vy
      [4] angle_index / 64.0   — direction in [0, 1)

    Player features: [px / 304.0, py / 224.0] — wall proximity awareness.
    """

    def __init__(self, npz_path, max_bullets=300, max_samples=None):
        data = np.load(npz_path, allow_pickle=False)
        self.px = data['px']
        self.py = data['py']
        self.moves = data['moves']
        self.survival_remaining = data['survival_remaining']
        self.n_bullets = data['n_bullets']
        self.bullet_offsets = data['bullet_offsets']
        self.bullet_xs = data['bullet_xs']
        self.bullet_ys = data['bullet_ys']
        self.bullet_angles = data['bullet_angles']
        self.max_bullets = max_bullets

        if max_samples:
            N = min(max_samples, len(self.px))
            self.px = self.px[:N]
            self.py = self.py[:N]
            self.moves = self.moves[:N]
            self.survival_remaining = self.survival_remaining[:N]
            self.n_bullets = self.n_bullets[:N]
            self.bullet_offsets = self.bullet_offsets[:N]

        total_b = int(self.n_bullets.sum())
        print(f"Loaded {len(self)} samples, {total_b} bullets "
              f"({total_b / max(len(self), 1):.1f} avg/frame)")

    def __len__(self):
        return len(self.px)

    def __getitem__(self, idx):
        px_val = float(self.px[idx])
        py_val = float(self.py[idx])
        offset = int(self.bullet_offsets[idx])
        n = min(int(self.n_bullets[idx]), self.max_bullets)

        bx = self.bullet_xs[offset:offset + n]
        by = self.bullet_ys[offset:offset + n]
        ang = self.bullet_angles[offset:offset + n]

        bullets = np.zeros((self.max_bullets, 5), dtype=np.float32)
        mask = np.zeros(self.max_bullets, dtype=np.float32)

        if n > 0:
            ang_idx = (ang & 63).astype(np.int32)
            vx = _VEL[ang_idx, 0]
            vy = _VEL[ang_idx, 1]
            bullets[:n, 0] = (bx - px_val) / 304.0
            bullets[:n, 1] = (by - py_val) / 224.0
            bullets[:n, 2] = vx
            bullets[:n, 3] = vy
            bullets[:n, 4] = ang.astype(np.float32) / 64.0
            mask[:n] = 1.0

        player = np.array([px_val / 304.0, py_val / 224.0], dtype=np.float32)
        return (
            torch.from_numpy(bullets),
            torch.from_numpy(mask),
            torch.from_numpy(player),
            torch.tensor(BITS_TO_IDX.get(int(self.moves[idx]), 0), dtype=torch.long),
            torch.tensor(self.survival_remaining[idx] / 60.0, dtype=torch.float32),
        )


def train_epoch(model, loader, optimizer, device):
    model.train()
    total_p, total_v, correct, total = 0.0, 0.0, 0, 0
    pbar = tqdm(loader, desc="  Train", leave=False)

    for bullets, mask, player, move, survival in pbar:
        b, m, p = bullets.to(device), mask.to(device), player.to(device)
        mo, sv = move.to(device), survival.to(device)

        policy, value = model(b, m, p)
        p_loss = F.cross_entropy(policy, mo)
        v_loss = F.mse_loss(value, sv)
        loss = p_loss + 0.5 * v_loss

        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        optimizer.zero_grad()

        total_p += p_loss.item()
        total_v += v_loss.item()
        correct += (policy.argmax(1) == mo).sum().item()
        total += mo.size(0)
        pbar.set_postfix(acc=f"{100 * correct / total:.1f}%")

    return (total_p / len(loader), total_v / len(loader),
            100.0 * correct / total)


@torch.no_grad()
def validate(model, loader, device):
    model.eval()
    total_p, total_v, correct, total = 0.0, 0.0, 0, 0

    for bullets, mask, player, move, survival in loader:
        b, m, p = bullets.to(device), mask.to(device), player.to(device)
        mo, sv = move.to(device), survival.to(device)

        policy, value = model(b, m, p)
        total_p += F.cross_entropy(policy, mo).item()
        total_v += F.mse_loss(value, sv).item()
        correct += (policy.argmax(1) == mo).sum().item()
        total += mo.size(0)

    return (total_p / len(loader), total_v / len(loader),
            100.0 * correct / total)


def train(args):
    device = torch.device('cpu')
    full = BulletDataset(args.data, max_bullets=args.max_bullets,
                         max_samples=args.max_samples)
    val_size = int(len(full) * args.val_split)
    train_size = len(full) - val_size
    train_ds, val_ds = random_split(
        full, [train_size, val_size],
        generator=torch.Generator().manual_seed(42))

    print(f"Train: {train_size}  Val: {val_size}  "
          f"(split {1 - args.val_split:.0%}/{args.val_split:.0%})")

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True,
                              num_workers=args.num_workers, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False,
                            num_workers=args.num_workers, pin_memory=True)

    model = PolicyValueNet(max_bullets=args.max_bullets).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    scheduler = CosineAnnealingLR(optimizer, T_max=args.epochs,
                                  eta_min=args.lr * 0.01)

    start_epoch = 0
    best_val_loss = float('inf')
    patience_counter = 0
    save_path = args.output or "training_data/policy_value_net.pt"
    os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else '.',
                exist_ok=True)

    if args.resume and os.path.exists(args.resume):
        ckpt = torch.load(args.resume, map_location=device, weights_only=False)
        model.load_state_dict(ckpt['model'])
        optimizer.load_state_dict(ckpt.get('optimizer', optimizer.state_dict()))
        start_epoch = ckpt.get('epoch', 0)
        best_val_loss = ckpt.get('best_val_loss', float('inf'))
        print(f"Resumed epoch {start_epoch}, best val loss {best_val_loss:.4f}")

    print(f"Training {train_size} samples, {args.epochs} epochs, "
          f"batch={args.batch_size}, lr={args.lr}")

    for epoch in range(start_epoch, args.epochs):
        p_loss, v_loss, acc = train_epoch(model, train_loader, optimizer, device)
        val_p, val_v, val_acc = validate(model, val_loader, device)
        val_total = val_p + 0.5 * val_v

        scheduler.step()
        lr_now = scheduler.get_last_lr()[0]

        print(f"Epoch {epoch + 1:3d}/{args.epochs} | "
              f"train: p={p_loss:.4f} v={v_loss:.4f} acc={acc:.1f}% | "
              f"val: p={val_p:.4f} v={val_v:.4f} acc={val_acc:.1f}% | "
              f"lr={lr_now:.2e}")

        if val_total < best_val_loss:
            best_val_loss = val_total
            patience_counter = 0
            torch.save({
                'model': model.state_dict(),
                'optimizer': optimizer.state_dict(),
                'epoch': epoch + 1,
                'best_val_loss': best_val_loss,
            }, save_path)
            print(f"  → saved (best val={best_val_loss:.4f})")
        else:
            patience_counter += 1

        if patience_counter >= args.patience:
            print(f"Early stop at epoch {epoch + 1}")
            break

    print(f"\nBest val_loss: {best_val_loss:.4f}  →  {save_path}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="Train DeepSet policy+value NN on beam search data")
    p.add_argument("--data", type=str, default="training_data/combined.npz")
    p.add_argument("--epochs", type=int, default=100)
    p.add_argument("--batch_size", type=int, default=1024)
    p.add_argument("--lr", type=float, default=0.001)
    p.add_argument("--max_samples", type=int, default=None)
    p.add_argument("--max_bullets", type=int, default=300)
    p.add_argument("--num_workers", type=int, default=0)
    p.add_argument("--val_split", type=float, default=0.2)
    p.add_argument("--patience", type=int, default=10)
    p.add_argument("--output", type=str, default="training_data/policy_value_net.pt")
    p.add_argument("--resume", type=str, default=None)
    args = p.parse_args()

    if not os.path.exists(args.data):
        print(f"Data file not found: {args.data}")
        print("Run:  python3 tools/gen_training_data.py --combine")
        sys.exit(1)

    train(args)
