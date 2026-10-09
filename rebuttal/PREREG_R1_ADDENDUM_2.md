# Pre-registration addendum 2 (committed before any analysis below is run)

Written 2026-10-09 after the strategy review of the 2026-10-08 report. It extends
PREREG_R1.md; nothing in that document is changed. Everything here that was not
in PREREG_R1.md is labelled **exploratory**. Deadlines: experiments finished by
2026-10-10 09:00 PT, freeze 2026-10-10 12:00 PT.

## A. Task 4 reporting (no new labels)

1. The NaN convention (whether NaN that arises only when training diverges counts
   as supported use) **was not fixed in advance**. The narrow reading was applied
   while labelling; the broad reading is the flip of every site tagged
   `divergence_only`. Both are reported, neither is chosen after the fact. The
   headline is the pair: 4 of 48 and 16 of 48 applicable sites.
2. All REACHABLE_UNGUARDED sites under the narrow reading are listed, one row per
   site, with file, line and pinned SHA (four sites in three files).
3. Split of applicable sites into verdict/selection (`kind` V) and other (`kind`
   O), under each reading, with exact Clopper-Pearson 95% intervals and a
   two-sided Fisher exact test on the 2x2 table (positive/negative by V/O).
   The strategy agent's hand figures to verify are 1/27 against 3/21, p about 0.3.
   Computed from `rebuttal/results/task4c_labels.json`; labels are not edited.

## B. Detector 2 null with 20 replicates (exploratory)

A replicate is an independent paired 5-seed comparison of two no-leak arms:
for s = 0..4 a fresh data draw (data seed 5000 + 10r + s, never used before) and
two models trained on that same source set with 0% leakage and different model
seeds (7000 + 100r + 10s and 7001 + 100r + 10s). The probe loss of arm Y is
compared with arm X within the draw; the five relative deltas go through the
shipped rule `flag_from_relative` (every delta negative and t <= -2.132, df 4).
Replicates r = 1..20. Report flags/20 with an exact Clopper-Pearson 95% interval.
Same model, protocol, epochs and stays as the detector 2 demo (small model, 900
stays nominal, 3 epochs, CPU).

**Reading, fixed now.** 3 or fewer flags of 20 is consistent with a 5% false
positive rate; 4 or more is reported as a limitation of detector 2's null
behaviour. Neither outcome is changed afterwards. Label: exploratory.

## C. Task 5a-prime: downstream AUROC on the full held-out target site (exploratory)

The 5a target probe has about 3 to 7 positive stays per seed, so it cannot
resolve a change of 0.01. 5a-prime evaluates the same pipeline on every Site B
stay that is not in the seed's drawn target sample (disjoint, so no stay seen in
pretraining at any leakage level).

- Encoders from 5a were not saved. The models are therefore retrained under the
  identical seeds (42..46), levels (0, 5, 20, 100%), code, epochs and CPU
  environment; as an identity check the retrained probe losses are compared with
  the committed 5a files and any difference is reported. No other change.
- Logistic head fitted on source exactly as in 5a. Target AUROC on the full
  held-out site; change versus the 0% arm per seed; mean and t interval (df 4);
  number of target positives reported.
- Gate: only if the first seed projects to finish all five within 3 hours of
  background CPU; otherwise stopped and reported as not run.

**Reading, fixed now.** If the 95% interval of the change excludes zero at a
level, a direction is established at that level for this pipeline. If intervals
still include zero with several hundred positives, the downstream metric cannot
see this leakage at this scale. Both outcomes are reported as found.

## D. Detector 5 composition ratio: per-seed archive and Type 2 prediction

1. Re-run the archived sampling study with the shipped `run(seed, n)` for
   n = 1200 (seeds 0..4) and n = 4000 (seeds 0..4; the archive has seeds 0..2);
   archive the per-seed composition_gap_ratio, availability ratio and flag for
   the positive and the negative case. Detector code is not touched.
2. Type 2 prediction for the positive case: P(flag) = Phi((mean - 0.30) / sd),
   mean and sd over seeds of composition_gap_ratio, compared with the observed
   flag count and an exact interval. The hand estimates to verify are about 0.42
   (n = 1200, observed 2/5) and about 0.24 (n = 4000, observed 0/3), computed first
   from the archived summary statistics (mean 0.283, sd 0.082; mean 0.274, sd
   0.036) and then from the re-archived per-seed values. The same prediction is
   given for the Task 6 sizes (n = 900 and 1500).
3. One sentence reconciles 3/5 (Task 6) with 2/5 (n = 1200).
4. The one-seed `detectors/results/external5.json` is replaced by the output of
   the unchanged `detectors/external/run_external5.py --seeds 5`; the old file
   stays in git history.

## E. Spot checks

The user labels the 12 sites without seeing the labeller's labels, which are not
shared until the user's are received. Report k of 12 agreement with an exact
interval (not a blind relabel), per task and pooled.

## F. Ledger

Every new number goes into LEDGER.md and STATUS.md the day it is produced.
