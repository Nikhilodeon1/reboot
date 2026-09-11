# Provenance

## Authorship

Anonymized for review. Development used Claude (Anthropic) as a coding and
analysis assistant.

## History

Exported without development history, because commit metadata identifies the
authors. The history is preserved and will be released with the de-anonymized
repository. It shows the detector 5 pre-registration
(`detectors/PREREGISTRATION.md`) committed before the external-validation code
whose results it governs; anonymized patches of those two commits, with their
full hashes, are in `detectors/preregistration_evidence/`.

## Deliberately absent

Per-stay caches derived from restricted clinical data (`full_labels.npz`,
`full_d5_arrays.npz`, `full_d2_pools.pkl`) are excluded by `.gitignore`, per the
PhysioNet data use agreement. Aggregate results are in
`detectors/results/*.json`. Regenerate the caches with your own credentials via
`detectors/TODO.md` section 0; `run_all.py` does not need them.

## Lost

Detector 1's full-scale logs (`full1_probe.out`, `full1_bootstrap.out`) were
empty when copied off the machine that ran them. Detector 1's full-scale figures
are transcribed from run output. Detectors 2 and 5 are backed by
`detectors/logs/full2.out` and `detectors/logs/full5.out`.
