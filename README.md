# Clean Verdicts Without Evidence

Code, tests, specification documents and aggregate results for *Clean Verdicts Without Evidence: An Audit of Five Clinical
Confound Detectors* (under review; anonymized).

## Layout

    detectors/          the five detectors (checks/), their tests, baselines and third-party scans; frozen
    src/, config.py     data loaders and the small model that detectors 1, 2 and 5 use
    v2/scripts/         one script per experiment (see each docstring)
    v2/results/         aggregate result files
    v2/patched_detectors/  copies of the detectors with an explicit "undecidable" verdict
    v2/battery/         label sheet for the external-library test
    v2/validation_kit/  material for applying the reporting standard to external diagnostics
    v2/evidence_r1/     first-round specifications, results and ledger
    v2/PREREG_*.md      specification documents; PREREG_MANIFEST.txt lists each one's commit and hash
    v2/EXPERIMENT_STATUS.md  which results were fixed in advance and which were exploratory
    v2/LEDGER_V2.md     every number with its source file and command
    v2/CITATIONS_V2.md  citation log
    v2/paper/           the manuscript; make_figs.py rebuilds its figures

## Install and test

Python 3.14, CPU only.

    pip install -r requirements.txt
    python -m pytest detectors/tests

Without the credentialed or PhysioNet data, 108 tests pass and 7 are skipped.

## Reproduce

    python v2/scripts/reproduce.py

reruns the experiments that need no data, in a scratch copy, and compares each result file with the committed one. Options
add the experiments on public files, on the benchmark's data file and on credentialed data; see the docstring.

    PCL_TEST_MODE=1 python detectors/run_all.py

reproduces the detectors' internal validation table (last line: `TOTAL  TP=6  FP=0  FN=1  TN=12 prec=1.00 rec=0.86 fpr=0.00`).

Two scripts install and run third-party code and are meant for a disposable hosted runtime:
`v2/scripts/e21_tableshift_run.py` and `v2/scripts/e23_battery.py`.

## Data

No patient-level data and no per-stay arrays are included. MIMIC-IV, eICU-CRD and the PhysioNet 2019 challenge data need
PhysioNet access; point the loaders at local copies with `MIMIC_DIR`, `EICU_DIR` and `PHYSIONET_DIR`.
