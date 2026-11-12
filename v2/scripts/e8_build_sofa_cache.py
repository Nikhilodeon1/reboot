"""E8 stage 1 (PREREG_V2_ADDENDUM_4.md): read the SOFA components once with the shipped functions and cache them in shards.

    python -W ignore v2/scripts/e8_build_sofa_cache.py --site mimic --data <mimiciv/3.1 dir> --out <dir outside the repo>
    python -W ignore v2/scripts/e8_build_sofa_cache.py --site eicu  --data <eicu-crd/2.0 dir> --out <dir outside the repo>

Calls the shipped mimic_sofa_components / eicu_sofa_components unchanged. Resumable at stage granularity: a finished site writes
DONE_<site> last, and a rerun exits at once. Shards are written atomically (temp file, then rename). The output holds patient-level
derivatives of credentialed data: keep it outside the repository and on private storage.
"""
import os
import sys
import gzip
import time
import pickle
import argparse

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)

SHARD = 2000


def atomic_dump(obj, path):
    tmp = path + ".tmp"
    with gzip.open(tmp, "wb", compresslevel=3) as fh:
        pickle.dump(obj, fh, protocol=pickle.HIGHEST_PROTOCOL)
    os.replace(tmp, path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", choices=["mimic", "eicu"], required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    done = os.path.join(a.out, f"DONE_{a.site}")
    if os.path.exists(done):
        print("already done", flush=True)
        return
    t0 = time.time()
    if a.site == "mimic":
        from src.data.mimic4 import load_stays
        from src.data.sofa_sepsis import mimic_sofa_components
        stays = load_stays(a.data)
        ids = stays["stay_id"].astype(int).values
        suspicion, C_by, _, infected, _ = mimic_sofa_components(a.data, stays)
    else:
        from src.data.sofa_sepsis import eicu_sofa_components
        pats = pd.read_csv(os.path.join(a.data, "patient.csv.gz"), usecols=["patientunitstayid", "unitdischargeoffset"],
                           encoding_errors="replace")
        pats = pats[pats["unitdischargeoffset"] / 60.0 >= 24].reset_index(drop=True)
        ids = pats["patientunitstayid"].astype(int).values
        suspicion, C_by, _, infected, _ = eicu_sofa_components(a.data, pats)
    print(f"components read in {time.time() - t0:.0f}s: {len(ids)} stays, {len(infected)} with suspected infection", flush=True)
    np.save(os.path.join(a.out, f"{a.site}_ids.npy"), ids)
    sids = sorted(int(s) for s in suspicion)
    n_shards = 0
    for k in range(0, len(sids), SHARD):
        chunk = {s: (float(suspicion[s]), C_by[s]) for s in sids[k:k + SHARD]}
        atomic_dump(chunk, os.path.join(a.out, f"{a.site}_shard_{k // SHARD:04d}.pkl.gz"))
        n_shards += 1
    open(done, "w").write(f"{len(ids)} stays, {len(sids)} suspected, {n_shards} shards, {time.time() - t0:.0f}s\n")
    print("done", flush=True)


if __name__ == "__main__":
    main()
