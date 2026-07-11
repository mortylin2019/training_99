#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
for s in "$HOME/.cargo/env" "$HOME/.cargo/env.sh"; do
  [ -f "$s" ] && source "$s" 2>/dev/null && break
done
if ! command -v cargo &>/dev/null; then
  echo "cargo not found. Install Rust: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
  exit 1
fi
echo "Building beam_core (${1:-release})..."
[ "${1:-}" = "debug" ] && cargo build || cargo build --release
PDIR="${1:-release}"; [ "$PDIR" = "debug" ] || PDIR="release"
SUF=$(python3 -c "import importlib.machinery; print(importlib.machinery.EXTENSION_SUFFIXES[0])")
cp "target/$PDIR/libbeam_core.so" "./beam_core${SUF}"
echo "beam_core${SUF} built"
python3 -c "import sys;sys.path.insert(0,'.');import beam_core;d,f=beam_core.score_pos_py(100.,100.,__import__('numpy').array([[104.,100.]]));assert f" && echo "OK"
