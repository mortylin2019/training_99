#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

# source cargo env
for s in "$HOME/.cargo/env" "$HOME/.cargo/env.sh"; do
  [ -f "$s" ] && source "$s" 2>/dev/null && break
done
if ! command -v cargo &>/dev/null; then
  echo "cargo not found. Install Rust: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
  exit 1
fi

MODE="${1:-release}"
FLAG=""; [ "$MODE" = "debug" ] || FLAG="--release"
PDIR="$MODE"; [ "$PDIR" = "debug" ] || PDIR="release"
SRC="target/$PDIR/"

# ── Linux (native) ──────────────────────────────────────
echo "=== Building beam_core for Linux ($MODE) ==="
cargo build $FLAG
cp "${SRC}libbeam_core.so" "./beam_core.cpython-312-x86_64-linux-gnu.so"
echo "  → beam_core.cpython-312-x86_64-linux-gnu.so"

# ── Windows (cross-compile from Linux: NOT recommended) ──
# MinGW ABI is incompatible with MSVC Python on Windows.
# Build on Windows natively: cargo build --release
if false && rustup target list --installed 2>/dev/null | grep -q x86_64-pc-windows-gnu; then
  echo "=== Building beam_core for Windows ($MODE) ==="
  cargo build $FLAG --target x86_64-pc-windows-gnu
  cp "target/x86_64-pc-windows-gnu/$PDIR/beam_core.dll" "./beam_core.cp312-win_amd64.pyd"
  echo "  → beam_core.cp312-win_amd64.pyd"
else
  echo "=== Skipping Windows build (target x86_64-pc-windows-gnu not installed) ==="
  echo "  Install: rustup target add x86_64-pc-windows-gnu"
fi

# ── Smoke test (Linux native only) ──────────────────────
echo "=== Smoke test ==="
python3 -c "
import sys; sys.path.insert(0,'.')
import beam_core, numpy as np
d,f = beam_core.score_pos_py(100.,100., np.array([[104.,100.]]))
assert f, 'collision detection failed'
print('OK')
"
echo "=== Done ==="
