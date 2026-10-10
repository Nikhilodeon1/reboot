# Report 2 for the strategy agent: experiments finished, ready to write

Written 2026-10-09 21:59 local time. Self-contained; it supersedes the earlier report where they
differ. Every number is in `rebuttal/LEDGER.md` with its source file, command and commit,
and everything up to remote head `0e438e3` is pushed (this report is committed after it). Freeze is 2026-10-10 12:00 PT.

## 1. State

All pre-registered work and both addenda are run. Pre-registration order is verifiable
from commit timestamps (prereg `25fc617`; addendum 2 `d14687a`, committed before its
analyses; addendum 3 `4918770` and 3b `69148a9`, committed before the full-scale runs;
frozen patterns, rubrics and labels for Tasks 3 and 4 before the corresponding scans).
Done: Tasks 0 to 6, the 20-replicate detector 2 null, 5a-prime, the detector 5 per-seed
archive, the full-scale detector 1 re-run, and the full-scale detector 2 and baseline
tier. Not done, by design: arms A3 and A4 at full scale (the caches lack the raw
pre-forward-fill series, so R is undetermined there), and the GPU runs (credentialed data
may not leave the owner's machine; the whole full-scale tier ran on CPU from existing
caches). One open item: the owner's 12 spot-check labels (k of 12 agreement will be
reported with an exact interval; the labeller's labels have not been shared).

## 2. The results, claim by claim

Direction of each: **C** confirms the paper, **W** weakens it, **N** new limitation.

| # | Claim in the paper | What the evidence now shows | Dir. |
|---|---|---|---|
| 1 | Detector 1 near-miss "got worse at full scale" (abstract, 6.2) | Two estimands were mixed. Like for like, the cohort-bootstrap flag probability is 0.216 (demo) and **0.241 observed at full scale** (predicted 0.217); the audit-draw figure 0.484 and its margin 0.06 reproduce. The demo could not resolve it; the coin flip at full scale stands. | W |
| 2 | eICU control is the discriminating counterexample | Observed margin 5.39 SD: a ceiling control. The only discriminating control is MIMIC window vs single-point (0.06). The eICU positive is at 2.59 (a discriminating positive). The eICU [-72,+24] control now has a dispersion (margin 291). | W |
| 3 | Detector 2's clean 0% control | Compared with itself, so it cannot flag. Exploratory null with 20 replicates: **1/20 flagged, CP95 [0.001, 0.249]**, reading met (3 or fewer). Caveat: three of 20 replicates had |t| above 2.132, and the null uses independent model seeds, harder than the detector's own shared-seed comparison. | C, qualified |
| 4 | Detector 2 values vs missingness | Demo: values-dominated (R = 0.02 and -0.11); prediction (mixed, 0.25 to 0.6) missed. Full scale: R undetermined (no A3). | W (demo) |
| 5 | Detector 2's effect is evidence of target exposure | **Corpus-size control, r2/r1: demo 0.31 (5%) and 0.48 (20%); full scale 0.55 and 0.69.** Both full-scale values exceed the pre-registered 0.5 line, so by the rule the effect is confounded with corpus size (reported as a new limitation; detector unchanged). Target exposure still adds beyond volume (A1 minus A2, t = 9.0 and 15.4). Detector 2's own full-scale deltas reproduce the paper's (-2.5, -7.6, -20.9% against -3.2, -7.4, -21.1%). | N, the most damaging |
| 6 | All three baselines fire at every level including 0% | True at demo scale. At full scale: k-fold silent at every level, external floor silent except 2/5 at 100%, only the train/test gap fires (including 0%). None carries information, but by missing the leakage, not by always firing. | W, nuanced |
| 7 | Leakage moves downstream performance in the expected direction | Demo probe (3 to 7 positives): intervals include zero. 5a-prime (13,880 target stays, about 287 positives): +0.0007, +0.0027, +0.0037 at 5/20/100%, only the last interval excludes zero (by a hair). Full scale (about 2,900 positives): no level distinguishable from zero. The effect is 2.6% of the baseline gap at most. | W |
| 8 | Detector 3 | 0 contaminated of 53 sampled sites (0/23 real selections, Wilson upper 0.14); 1 disclosed oracle; sensitivity undefined. Detector returns indeterminate on 53 of 53. Yang et al. built after three environment fixes, reports 0 on both fixtures and recognises no model pairing. | N |
| 9 | Type 1 beyond three repos | 4/48 (CP95 [0.023, 0.200]) narrow, 16/48 ([0.204, 0.484]) broad; verdict/selection against other sites 1/27 against 3/21 (p = 0.31) and 11/27 against 5/21 (p = 0.35). The convention was not fixed in advance; both are reported. Four positives, three files. | C, qualified |
| 10 | Detector 5 false negative "0.27 against 0.30" | The mean of a quantity that straddles the gate: flagged in 3/5 seeds (Task 6) and 2/5 (n = 1200); the Type 2 prediction is 0.42 (hand estimate confirmed) and 0.15 at n = 4000 (0/5). Restricted to MAP and HH the flagship is flagged 5/5, but the ratio is unstable on controls, so the composition gate is decorative on PhysioNet too. The one-seed `external5.json` is replaced by the five-seed result (precision 9/9, FPR 0/10). | W |
| 11 | Type 2 model for detector 1 | Predicted 0.475 against 0.484 observed; 0.217 against 0.241 at full scale (cohort bootstrap). | C |
| 12 | Prevalence-ratio baseline for detector 1 | Inverted at both scales (AUROC for picking mismatches 0.059 demo, 0.125 full). | C |

## 3. Decisions for the strategy agent

1. **How to frame the corpus-size result (row 5).** The pre-registered reading is fixed:
   "confounded with corpus size, a new limitation, detector not changed". The framing choice
   is placement and tone: lead the response with it, or place it in the limitations section
   with the demo and full values side by side. I recommend stating both numbers (0.31 and
   0.48 at demo, 0.55 and 0.69 at full) and the surviving fact (target exposure adds beyond
   volume, t = 9 to 15), and not restating the detector's claim as "validated".
2. **What goes in the 8-page paper and what stays in the response or appendix.** Rows 1,
   2, 3, 5, 6 and 7 each change a sentence in the main text; rows 4, 8 to 12 can go to the
   appendix. Net space is the constraint. I recommend: correct the abstract and 6.2 in place
   (row 1), replace the detector 2 and baseline sentences with the new numbers, and put the
   exploratory analyses (null with 20 replicates, 5a-prime) in an appendix labelled
   exploratory.
3. **Scale-dependence as a result, not an excuse (row 6).** The baselines flip from
   "fire everywhere" to "two silent" between scales. This supports the paper's own theme
   (scale changes diagnostics qualitatively) and is a statement the paper can make with
   data. Confirm it should be framed that way.
4. **Findings versus Proceedings.** The owner wants Proceedings. The honest concessions above
   (rows 1, 2, 5, 7, 10) are material; I recommend writing them in full and not hedging, because
   the pre-registration record is the paper's strongest asset.

## 4. Caveats that must not be dropped

Full scale uses cohorts of 74,607 and 130,446 stays (cache filters) for the detector 2 tier
and 74,829 and 132,900 for detector 1; arms A3 and A4 are demo only; the "900 stays per
site" at demo scale is nominal (602 to 651 source stays after the loader's filters);
variant A of detector 5 is the conjunction and variant B availability only; detector 3 and
Task 4 scans cover Python files only (126 notebooks not scanned, 8 unparseable); the
spot-check agreement is not a blind relabel; third-party tools were built and run only in
Docker; no patient-level data is in the repository and none left the owner's machine.

## 5. Timeline

Experiments are done (deadline was 2026-10-10 09:00). Next, in order: your answers to
section 3; the paper edits and the response draft; a pass checking every figure in the
text against the ledger; the owner's spot-check labels folded in; final push; the
4open.science mirror refresh after the freeze (12:00 PT).
