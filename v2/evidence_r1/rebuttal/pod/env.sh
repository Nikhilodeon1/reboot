# Source, do not execute:   . rebuttal/pod/env.sh
#
# Pod layout: the repo lives on the small persistent home disk; everything big
# and rebuildable (venv, uv cache, raw data, caches, checkpoints) lives under
# POD_SCRATCH, which is wiped when the pod is replaced. Only aggregate results
# are written back into the repo (data-use agreement: no per-stay files).
# Nothing here hard-codes a user name or home path.

_pod_here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export REPO_ROOT="$(cd "$_pod_here/../.." && pwd)"

export POD_SCRATCH="${POD_SCRATCH:-/tmp/reboot_scratch}"
export VENV="${VENV:-$POD_SCRATCH/venv}"
export UV_PYTHON_INSTALL_DIR="$POD_SCRATCH/uvpy"
export UV_CACHE_DIR="$POD_SCRATCH/uvcache"

# Dataset locations read by config.py. Stage the data here yourself.
export PHYSIONET_DIR="${PHYSIONET_DIR:-$POD_SCRATCH/data/physionet2019}"
export MIMIC_DIR="${MIMIC_DIR:-$POD_SCRATCH/data/mimic-iv}"
export EICU_DIR="${EICU_DIR:-$POD_SCRATCH/data/eicu}"

# Derived per-stay arrays and checkpoints: scratch only, never the repo.
export CACHE_DIR="${CACHE_DIR:-$POD_SCRATCH/cache}"
export CHECKPOINT_DIR="${CHECKPOINT_DIR:-$POD_SCRATCH/checkpoints}"

# Aggregate outputs only; this one is inside the repo and survives the pod.
export RESULTS_DIR="${RESULTS_DIR:-$REPO_ROOT/rebuttal/results}"

# One process per core when several runs share the GPU.
export NUM_WORKERS="${NUM_WORKERS:-0}"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}"

mkdir -p "$POD_SCRATCH" "$CACHE_DIR" "$CHECKPOINT_DIR" "$RESULTS_DIR" \
         "$PHYSIONET_DIR" "$MIMIC_DIR" "$EICU_DIR"

if [ -f "$VENV/bin/activate" ]; then
    . "$VENV/bin/activate"
fi
export PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}"
unset _pod_here
