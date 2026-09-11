"""Third-party repositories for detector 3 generalization. Parsed, never executed.

Commits pinned. Per-file ground truth in `rationale`. DomainBed is non-clinical.
"""
import os

# clone root; override with PCL_SCRATCH_REPOS
SCRATCH = os.environ.get(
    "PCL_SCRATCH_REPOS",
    os.path.join(os.path.expanduser("~"), ".cache", "pcl_scan_repos"))

TARGETS = [
    {
        "name": "DomainBed",
        "url": "https://github.com/facebookresearch/DomainBed",
        "commit": "b93c22a1cfc3b2428398272c1a116c8de1f4139e",
        "paper": "Gulrajani & Lopez-Paz, In Search of Lost Domain Generalization, ICLR 2021",
        "clinical": False,
        "files": [
            ("domainbed/model_selection.py", True,
             "Contains OracleSelectionMethod, whose own docstring states it "
             "'picks argmax(test_out_acc) across all hparams'. Selection is "
             "performed on the held-out TEST domain, which is precisely the "
             "confound detector 3 exists to find. The authors disclose it as an "
             "oracle, so ground truth here is documented, not inferred. The same "
             "file also contains IIDAccuracySelectionMethod, which selects on "
             "training-domain validation only, so a file-level verdict of "
             "CONTAMINATED is correct for the file as a whole."),
            ("domainbed/scripts/sweep.py", False,
             "Builds and launches job command lines across a hyperparameter "
             "grid. It never evaluates a model or compares scores, so no "
             "selection of any kind happens here; the choice of best run is "
             "made later in collect_results.py. A detector that flags this is "
             "reacting to the word 'sweep' rather than to selection."),
        ],
    },
    {
        "name": "mimic3-benchmarks",
        "url": "https://github.com/YerevaNN/mimic3-benchmarks",
        "commit": "ea0314c7cbd369f62e2237ace6f683740f867e3a",
        "paper": "Harutyunyan et al., Multitask learning and benchmarking with clinical time series data, Sci Data 2019",
        "clinical": True,
        "files": [
            ("mimic3models/in_hospital_mortality/logistic/main.py", False,
             "Fits a single LogisticRegression with C taken from a command-line "
             "argument. There is no loop over hyperparameters and therefore no "
             "selection at all. Both a validation and a test reader exist and "
             "both are scored, which is legitimate reporting -- the case "
             "detector 3 is specifically designed not to flag."),
            ("mimic3models/in_hospital_mortality/main.py", False,
             "Trains one Keras model per invocation with hyperparameters fixed "
             "from argparse, using a validation split for early stopping and "
             "checkpointing. Test data is read for final reporting only. No "
             "hyperparameter is chosen by comparing scores across candidates."),
        ],
    },
    {
        "name": "MIMIC_Extract",
        "url": "https://github.com/MLforHealth/MIMIC_Extract",
        "commit": "d8d2dea551283bea449b8495bfc1b5a41b90d837",
        "paper": "Wang et al., MIMIC-Extract, CHIL 2020",
        "clinical": True,
        "files": [],   # none declared
    },
    {
        "name": "HIRID-ICU-Benchmark",
        "url": "https://github.com/ratschlab/HIRID-ICU-Benchmark",
        "commit": "bee770094bf8389920bc09823895b87e09a563dd",
        "paper": "Yeche et al., HiRID-ICU-Benchmark, NeurIPS Datasets & Benchmarks 2021",
        "clinical": True,
        "files": [],   # none declared
    },
]


def resolved_files():
    """(repo, absolute path, expected_flag, rationale) per declared file."""
    out = []
    for t in TARGETS:
        for rel, exp, why in t["files"]:
            out.append((t["name"], os.path.join(SCRATCH, t["name"], rel),
                        exp, why))
    return out
