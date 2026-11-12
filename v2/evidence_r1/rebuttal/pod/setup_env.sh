#!/usr/bin/env bash
# Build the Python environment under POD_SCRATCH. Rerun after every new pod.
#
#   bash rebuttal/pod/setup_env.sh
#
# TORCH_INDEX picks the PyTorch wheel index. A V100 is compute capability 7.0,
# and some recent CUDA wheels drop it, so preflight.py checks the arch list and
# fails loudly instead of letting training fall back to CPU. If it fails, rerun
# with a different index, e.g.  TORCH_INDEX=https://download.pytorch.org/whl/cu118
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$here/env.sh"

TORCH_INDEX="${TORCH_INDEX:-https://download.pytorch.org/whl/cu126}"
PY_VERSION="${PY_VERSION:-3.12}"

if ! command -v uv >/dev/null 2>&1; then
    python3 -m pip install --user --quiet uv
    export PATH="$HOME/.local/bin:$PATH"
fi

# The system python3 can be too old; uv fetches its own into scratch.
uv python install "$PY_VERSION"
uv venv --python "$PY_VERSION" "$VENV"
. "$VENV/bin/activate"

# Not the pins in requirements.txt: those reproduce the committed CPU results.
# The pod needs a CUDA torch, so versions are recorded instead of pinned.
uv pip install numpy pandas scikit-learn matplotlib
uv pip install torch --index-url "$TORCH_INDEX"

uv pip freeze > "$RESULTS_DIR/pod_env_versions.txt"
echo "Package versions recorded in $RESULTS_DIR/pod_env_versions.txt"

python "$here/preflight.py"
