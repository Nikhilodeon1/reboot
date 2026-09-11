# Auditing the Auditor

Code, tests, run logs and aggregate results for *Auditing the Auditor: Four
Failure Modes of Confound Detection in Clinical Machine Learning* (under review).
Anonymized for double-blind review.

Five detectors, one per confound type:

| # | Confound | Module |
|---|---|---|
| 1 | Label-definition shift | `detectors/checks/check1_label_shift.py` |
| 2 | Pretraining leakage | `detectors/checks/check2_pretrain_leakage.py` |
| 3 | OOD-contaminated hyperparameter selection | `detectors/checks/check3_selection_audit.py` |
| 4 | Circular derived constraints | `detectors/checks/check4_circularity.py` |
| 5 | Missingness / scale artifacts | `detectors/checks/check5_missingness_scale.py` |

## Layout

    detectors/
      checks/       the five detectors
      harness.py    Case type, confusion counts, uncertainty rendering
      run_all.py    reproduces the results table
      run_seeds.py  multi-seed stability for detectors 1, 2, 5
      baselines/    standard evaluation checks, for comparison
      external/     full-scale and third-party validation
      fixtures/     historical buggy sweep and its fix (detector 3 ground truth)
      results/      aggregate results (JSON); scale per file in results/README.md
      logs/         run output
      tests/        unit and regression tests
    src/, config.py         data loaders and model used by detectors 1, 2, 5
    scripts/                training scripts from the underlying model; not used by the detectors
    TAXONOMY.md             the four diagnostic failure modes
    docs/RESULTS_NOTES.md   detailed results record
    detectors/PREREGISTRATION.md, PREREGISTRATION_OUTCOME.md
    detectors/preregistration_evidence/   anonymized patches fixing the pre-registration order

## Requirements

Python 3.14, CPU only.

    pip install -r requirements.txt

## Reproduce the results table

No clinical data needed.

    PCL_TEST_MODE=1 python detectors/run_all.py

Expected last line:

    TOTAL  TP=6  FP=0  FN=1  TN=12 prec=1.00 rec=0.86 fpr=0.00

Detectors 3 and 4 run live (static analysis). Detectors 1, 2 and 5 load
`detectors/results/check{1,2,5}.json`.

## Tests

    PCL_TEST_MODE=1 python -m unittest discover -s detectors/tests -t . -q

116 tests. Without PhysioNet data, 7 skip with `PhysioNet data not present`.

## Data

Not included. All three datasets require PhysioNet credentialing and a signed
data use agreement:

- PhysioNet/Computing in Cardiology Challenge 2019
- MIMIC-IV v3.1
- eICU-CRD v2.0

Point the loaders at local copies:

    export PHYSIONET_DIR=/path/to/physionet2019   # contains training_setA/, training_setB/
    export MIMIC_DIR=/path/to/mimiciv/3.1
    export EICU_DIR=/path/to/eicu-crd/2.0

Or place them under `data/` as `physionet2019/`, `mimic4-demo/`, `eICU-demo/`.
`data/` is gitignored. If `data/` is a symlink or junction, remove the link, not
its target.

## Run detectors on data

    python detectors/checks/check3_selection_audit.py
    python detectors/checks/check4_circularity.py
    PCL_TEST_MODE=1 python detectors/checks/check1_label_shift.py
    python detectors/checks/check5_missingness_scale.py 1200
    PCL_TEST_MODE=1 python detectors/checks/check2_pretrain_leakage.py --stays 900 --seeds 3 --epochs 3

Full-scale external runs and cache regeneration: `detectors/TODO.md`, section 0.

## Results

Internal validation suite, demonstration scale:

| Detector | TP/FP/FN/TN | Note |
|---|---|---|
| 1 label shift | 1/0/0/1 | κ 0.467 positive, 0.771 control |
| 2 pretraining leakage | 3/0/0/1 | detection floor 5% |
| 3 OOD selection | 1/0/0/1 | historical bug |
| 4 circularity | 1/0/0/8 | |
| 5 missingness/scale | 0/0/1/1 | false negative |
| **Total** | **6/0/1/12** | precision 1.00, recall 0.86 |

Full-scale external results, uncertainty and failure-mode findings:
`docs/RESULTS_NOTES.md` and the paper. Archived full-scale logs: `detectors/logs/full2.out` (detector 2),
`detectors/logs/full5.out` (detector 5). Scale of each result file:
`detectors/results/README.md`.

## Not included

- Per-stay caches derived from restricted data (`*.npz`, `*.pkl`). Regenerate
  via `detectors/TODO.md` section 0.
- Detector 1 full-scale logs (lost in transfer). Its full-scale figures are
  transcribed from run output.
- Development history. Commit metadata identifies the authors; released with the
  de-anonymized repository. The two commits that fix the pre-registration order
  are in `detectors/preregistration_evidence/`. See `CONTRIBUTORS.md`.

Absolute paths in `detectors/logs/` are redacted to `<repo>`.
