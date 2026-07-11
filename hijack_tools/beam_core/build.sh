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
echo "Building beam_core ($MODE)..."
[ "$MODE" = "debug" ] && cargo build || cargo build --release
PDIR="$MODE"; [ "$PDIR" = "debug" ] || PDIR="release"

# detect source library name (differs by OS)
SRC="target/$PDIR/"
if [ -f "${SRC}beam_core.dll" ]; then
  LIB="${SRC}beam_core.dll"
elif [ -f "${SRC}libbeam_core.so" ]; then
  LIB="${SRC}libbeam_core.so"
elif [ -f "${SRC}libbeam_core.dylib" ]; then
  LIB="${SRC}libbeam_core.dylib"
else
  echo "ERROR: cannot find built library in $SRC (expected .dll/.so/.dylib)"
  ls "$SRC" 2>/dev/null || true
  exit 1
fi

SUF=$(python3 -c "import importlib.machinery; print(importlib.machinery.EXTENSION_SUFFIXES[0])")
cp "$LIB" "./beam_core${SUF}"
echo "beam_core${SUF} built"

# smoke test
python3 -c "
import sys; sys.path.insert(0,'.')
import beam_core, numpy as np
d,f = beam_core.score_pos_py(100.,100., np.array([[104.,100.]]))
assert f, 'collision detection failed'
print('OK')
"
