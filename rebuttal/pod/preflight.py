"""Check the pod before any experiment is launched.

    . rebuttal/pod/env.sh && python rebuttal/pod/preflight.py

Exit status is nonzero if a hard requirement fails. Prints no paths outside the
configured directories and no host or user information.
"""
import os
import sys
import shutil

HARD_FAIL = []


def line(label, value):
    print(f"{label:<22}{value}")


def gb(n):
    return n / 1024 ** 3


def cgroup_mem_limit():
    for p in ("/sys/fs/cgroup/memory.max",
              "/sys/fs/cgroup/memory/memory.limit_in_bytes"):
        try:
            v = open(p).read().strip()
            if v.isdigit() and int(v) < 1 << 60:
                return int(v)
        except OSError:
            pass
    return None


def host_mem():
    try:
        for ln in open("/proc/meminfo"):
            if ln.startswith("MemTotal"):
                return int(ln.split()[1]) * 1024
    except OSError:
        return None


def main():
    line("python", sys.version.split()[0])
    line("cpu cores", os.cpu_count())

    limit, host = cgroup_mem_limit(), host_mem()
    if limit:
        line("ram (pod limit)", f"{gb(limit):.0f} GB")
    if host:
        note = "  <- ignore, pod limit above applies" if limit else ""
        line("ram (host view)", f"{gb(host):.0f} GB{note}")

    try:
        import torch
        line("torch", torch.__version__)
        if not torch.cuda.is_available():
            HARD_FAIL.append("torch.cuda.is_available() is False")
        else:
            cap = torch.cuda.get_device_capability(0)
            sm = f"sm_{cap[0]}{cap[1]}"
            arches = torch.cuda.get_arch_list()
            props = torch.cuda.get_device_properties(0)
            line("gpu", f"{props.name}, {gb(props.total_memory):.0f} GB, {sm}")
            line("torch arch list", " ".join(arches))
            if sm not in arches:
                HARD_FAIL.append(
                    f"this torch build has no kernels for {sm}; "
                    "rerun setup_env.sh with a different TORCH_INDEX")
    except ImportError:
        HARD_FAIL.append("torch not importable (run setup_env.sh)")

    repo = os.environ.get("REPO_ROOT", ".")
    scratch = os.environ.get("POD_SCRATCH", "/tmp")
    for label, path, floor in (("repo disk free", repo, 1.0),
                               ("scratch disk free", scratch, 25.0)):
        try:
            free = gb(shutil.disk_usage(path).free)
            flag = "" if free >= floor else f"  <- below {floor:.0f} GB floor"
            line(label, f"{free:.1f} GB{flag}")
            if flag and label.startswith("scratch"):
                HARD_FAIL.append("scratch disk below floor")
        except OSError:
            line(label, "unavailable")

    for var in ("PHYSIONET_DIR", "MIMIC_DIR", "EICU_DIR", "CACHE_DIR",
                "CHECKPOINT_DIR", "RESULTS_DIR"):
        p = os.environ.get(var)
        if not p:
            line(var, "UNSET (source rebuttal/pod/env.sh)")
            HARD_FAIL.append(f"{var} unset")
            continue
        n = len(os.listdir(p)) if os.path.isdir(p) else -1
        line(var, "missing" if n < 0 else f"{n} entries")

    in_repo = os.path.realpath(os.environ.get("CACHE_DIR", "")).startswith(
        os.path.realpath(repo))
    if in_repo:
        HARD_FAIL.append("CACHE_DIR is inside the repo; per-stay arrays must "
                         "stay out of it")

    print()
    if HARD_FAIL:
        print("PREFLIGHT FAILED:")
        for m in HARD_FAIL:
            print("  -", m)
        sys.exit(1)
    print("PREFLIGHT OK")


if __name__ == "__main__":
    main()
