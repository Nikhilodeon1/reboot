











import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("PCL_TEST_MODE", "0")

from config import TEST_MODE, CACHE_DIR
assert not TEST_MODE, "Set PCL_TEST_MODE=0 (source runpod_env.sh) for a prod cache."

from run_paper_experiments import load_all_data

ds, pn, mimic, eicu = load_all_data()
print(f"\nCache built in {CACHE_DIR}")
print(f"  PhysioNet={len(pn)}  MIMIC-IV={len(mimic)}  eICU={len(eicu)}")
import numpy as np
for name, s in (("MIMIC", mimic), ("eICU", eicu)):
    if s:
        print(f"  {name} sepsis+ rate: {np.mean([x['label'][0] for x in s]):.3f}")
