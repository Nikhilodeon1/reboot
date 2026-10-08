# Pod setup

The repository lives on the small persistent home disk. The virtual environment,
raw data, derived arrays and checkpoints live under `POD_SCRATCH` (default
`/tmp/reboot_scratch`), which is lost when the pod is replaced. Only aggregate
outputs are written into the repository (`rebuttal/results/`).

After every new pod:

```bash
git clone <anonymized-repo-url> reboot && cd reboot
bash rebuttal/pod/setup_env.sh        # venv, CUDA torch, versions recorded, preflight
```

In every new shell:

```bash
. rebuttal/pod/env.sh                 # sets paths, activates the venv
python rebuttal/pod/preflight.py
```

Raw datasets are not fetched by anything here. Stage them into `PHYSIONET_DIR`,
`MIMIC_DIR` and `EICU_DIR` (printed by `preflight.py`), subject to the data-use
agreements. `CACHE_DIR` and `CHECKPOINT_DIR` hold per-stay arrays; preflight
fails if `CACHE_DIR` is inside the repository.

A V100 is compute capability 7.0. If preflight reports that the installed torch
has no `sm_70` kernels, rerun with another wheel index, for example
`TORCH_INDEX=https://download.pytorch.org/whl/cu118 bash rebuttal/pod/setup_env.sh`.

## CPU-only pod

Task 2's demo tier runs on CPU. On a pod without a GPU use the CPU torch wheel
and tell preflight not to require one:

```bash
TORCH_INDEX=https://download.pytorch.org/whl/cpu REQUIRE_GPU=0 bash rebuttal/pod/setup_env.sh
```
