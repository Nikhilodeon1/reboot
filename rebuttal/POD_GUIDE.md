# Running experiments on a small-persistent-disk pod: a practical guide

This is what we learned running CPU and GPU experiments on a rented notebook pod that has a small persistent home
disk (5 GB) and a large wiped-on-restart scratch disk. It is written for someone who has never used the pod.
It contains no names, hostnames or credentials.

## 1. What the pod is

- **Persistent home, 5 GB.** Survives a pod crash or restart. Put only the code repository and small result files here.
  Our repository was about 1.1 GB, so the room for anything else is small.
- **Scratch, under `/tmp`.** Large and fast, but wiped when the pod is replaced or crashes. Put the Python environment,
  raw data, derived arrays and checkpoints here, and expect to rebuild them.
- **Resources vary by pod.** We were offered a 12-vCPU 32 GB A40, a 16-core 64 GB V100 and a 32-vCPU 64 GB CPU-only pod.
  `free -h` and `os.cpu_count()` show the host (one pod reported 376 GB and 80 cores), not your limit.
  Read the real limits from the container: `cat /sys/fs/cgroup/memory.max` for memory. The preflight script below
  prints both.

## 2. Rules we followed

- **Credentialed data stays off the pod unless the data-use agreement allows it.** MIMIC-IV and eICU-CRD are credentialed.
  Our experiments on them ran on a local machine from existing caches. The pod was used for the open PhysioNet 2019 data
  and for code that needs no clinical data. Check your own agreement. If you do upload, delete the data when you finish.
- **Only aggregate outputs go back into the repository.** No per-patient or per-stay files. Derived per-stay arrays stay
  under scratch, never in the repository (the preflight script fails if the cache directory is inside the repo).
- **Push before you start the pod.** The pod clones from your remote. If a script is missing on the pod, it is almost always
  because it was committed locally and not pushed.
- **Do not upload a large `.tgz` and expect it to extract in place.** An uploaded archive lands in the home directory. Extract it
  into the directory you intend with `tar -xzf file.tgz -C target_dir`, then `ls target_dir` to confirm.

## 3. First-time setup (every new pod)

```bash
git clone <your-repo-url> project && cd project
bash pod/setup_env.sh          # builds the venv under scratch, records package versions, runs preflight
```

In every new shell:

```bash
. pod/env.sh                   # sets paths, activates the venv
python pod/preflight.py        # prints RAM limit, cores, GPU, free disk; exits nonzero on a hard failure
```

CPU-only pod:

```bash
TORCH_INDEX=https://download.pytorch.org/whl/cpu REQUIRE_GPU=0 bash pod/setup_env.sh
```

V100 (compute capability 7.0): some recent CUDA wheels no longer ship kernels for it. If preflight reports no `sm_70`
kernels, rerun with an older wheel index:

```bash
TORCH_INDEX=https://download.pytorch.org/whl/cu118 bash pod/setup_env.sh
```

## 4. The three small scripts

`pod/env.sh` (source it, do not run it):

```bash
_here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export REPO_ROOT="$(cd "$_here/.." && pwd)"
export POD_SCRATCH="${POD_SCRATCH:-/tmp/project_scratch}"
export VENV="${VENV:-$POD_SCRATCH/venv}"
export UV_PYTHON_INSTALL_DIR="$POD_SCRATCH/uvpy"
export UV_CACHE_DIR="$POD_SCRATCH/uvcache"
export DATA_DIR="${DATA_DIR:-$POD_SCRATCH/data}"
export CACHE_DIR="${CACHE_DIR:-$POD_SCRATCH/cache}"
export CHECKPOINT_DIR="${CHECKPOINT_DIR:-$POD_SCRATCH/checkpoints}"
export RESULTS_DIR="${RESULTS_DIR:-$REPO_ROOT/results}"      # small, aggregate, inside the repo
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"               # one thread per process; run one process per core
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}"
mkdir -p "$POD_SCRATCH" "$DATA_DIR" "$CACHE_DIR" "$CHECKPOINT_DIR" "$RESULTS_DIR"
[ -f "$VENV/bin/activate" ] && . "$VENV/bin/activate"
export PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}"
```

`pod/setup_env.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$here/env.sh"
TORCH_INDEX="${TORCH_INDEX:-https://download.pytorch.org/whl/cu126}"
PY_VERSION="${PY_VERSION:-3.12}"
command -v uv >/dev/null 2>&1 || { python3 -m pip install --user --quiet uv; export PATH="$HOME/.local/bin:$PATH"; }
uv python install "$PY_VERSION"            # the system python can be too old; uv fetches its own into scratch
uv venv --python "$PY_VERSION" "$VENV"
. "$VENV/bin/activate"
uv pip install numpy pandas scikit-learn matplotlib
uv pip install torch --index-url "$TORCH_INDEX"
uv pip freeze > "$RESULTS_DIR/pod_env_versions.txt"     # record versions instead of pinning for CUDA
python "$here/preflight.py"
```

`pod/preflight.py` should check, and exit nonzero when a hard requirement fails: the container memory limit
(`/sys/fs/cgroup/memory.max`) against the host view, `torch.cuda.is_available()` (unless `REQUIRE_GPU=0`), that the GPU's
`sm_XX` appears in `torch.cuda.get_arch_list()`, free disk on the repository (at least 1 GB) and on scratch (at least
25 GB), and that the cache directory is not inside the repository.

## 5. Habits that saved time

- **Expect to lose the environment.** One pod crashed and took the venv with it, while the persistent home survived. Because the
  whole environment is rebuilt by `setup_env.sh`, recovery was a clone, a setup run and a relaunch.
- **Run seeds in parallel, one process per core.** Set the thread variables to 1 first. A single demonstration-scale
  run of one of our detectors took about 6.5 minutes on a CPU pod, so five seeds in parallel took the same time as one.
- **Time one run before launching the batch.** It tells you the cores and memory you need.
- **Check results before copying them back.** Compare a re-run of one archived number against the stored one, so you know
  the pod environment reproduces your local results.
- **Bring results home as a small archive.** Tar only the aggregate JSON and CSV files, download or upload the archive, and commit
  them from your own machine. Do not give the pod credentials for your repository.
- **Close memory-hungry apps locally** before running anything on the full cohort on your own machine.

## 6. Checklist before you leave a pod

1. Aggregate results are committed from your machine, and the file counts match what the pod produced.
2. No per-patient or per-stay files exist inside the repository. Run `git status` and look.
3. Raw credentialed data you uploaded is deleted from the pod, if you uploaded any.
4. Package versions are recorded (`pod_env_versions.txt`) with the results.
