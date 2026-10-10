# Rebuttal status

Freeze 2026-10-10 12:00 PT. Response submitted evening of 2026-10-11.

## 2026-10-06

**Task 0 — done.** `PREREG_R1.md` + empty `LEDGER.md` committed alone as
`25fc617`, 2026-10-06 09:06:04 -0700, before any rebuttal code existed.
Three deviations from the task prompt declared in advance (rebuttal path, Task 2
leak-size convention, A2 applicability).

**Task 1 — done.** `rebuttal/scripts/task1_stats.py`, CPU, no clinical data.
All five hand-check targets supplied with the task reproduce exactly:
precision 6/6 lower bound 0.541, FPR 0/12 upper bound 0.265, recall 6/7
[0.421, 0.996], MIMIC full predicted P(flag) 0.475 vs 0.484 observed, MIMIC demo
0.211 predicted vs 0.216 observed, eICU full ~0 vs 0.000.

### Two results that change what the paper may claim

**1. The paper's demo→full P(flag) comparison mixes two estimands.**
§6.2 and the abstract say the control flags 48.4% of the time at full scale,
"worse than at 1/640th the data, not better", citing P(flag)=0.216 at n=117.
Those two numbers are not the same quantity:

| | demo (n=117) | full (n=74,829) |
|---|---|---|
| cohort bootstrap P(κ≤0.60) | **0.216** (archived) | **0.217** (predicted; the observed value was never archived) |
| audit-draw P(flag) | **0.000**, degenerate — min(500,117)=117 drawn without replacement, so the audit subset *is* the cohort and has zero variance | **0.484** (archived) |

Like-for-like on the cohort bootstrap, the flag probability is ~0.22 at both
scales. The demo κ CI [0.527, 0.774] also contains the full-cohort value 0.602,
so the two estimates are not statistically distinguishable. The claim that the
near-miss "got worse with data" does not survive in its current form.

What does survive, and is still a Type 2 result: at full scale the population κ
is 0.602 against a threshold of 0.60, and at the detector's operating point the
verdict is a coin flip, P(flag)=0.484, predicted 0.475 by the pre-registered
model. The honest framing is that the demo cohort could not resolve this at all,
not that more data made it worse.

**2. Under the pre-registered margin rule, only one control in the paper is
discriminating — and it is the coin-flip one.**
Rule fixed in the prereg: discriminating iff m = |τ − statistic| / SD ≤ 3.

| detector 1 control | scale | m | class |
|---|---|---|---|
| MIMIC win vs single-point | full | 0.06 | discriminating |
| MIMIC win[-24,+12] | full | 17.0 | ceiling |
| MIMIC win[-72,+24] | full | 77.0 | ceiling |
| eICU win vs single-point | full | 5.40 | **ceiling** |
| eICU win[-24,+12] | full | 36.9 | ceiling |
| eICU win[-72,+24] | full | MISSING (SD 0) | MISSING |

The paper reports eICU's win-vs-single-point control as the discriminating
counterexample. By the pre-registered rule it is a ceiling control at 5.4 SD.
So detector 1 has exactly one discriminating control across both databases, and
it is the one whose verdict is arbitrary. The "TN=3 (1 discriminating,
2 non-discriminating)" wording needs replacing with the margin numbers.

Seven of the fifteen control margins are MISSING: no dispersion was archived for
detector 2's 0% control or for either detector 5 control, and the demo detector 1
audit draws are degenerate. That is itself the answer to Npus on uneven
validation depth.

### Operational notes

- `data/` junction is absent after the repo split and must be recreated before
  any data-touching task (Task 2, 5a, 5c, 6).
- The 18-repo scan corpus must be re-cloned at the SHAs in `SCAN_CORPUS.md`
  (Tasks 3, 4).
- Confirmed available: GitHub API (Task 4a sampling), Docker (Task 3f gate).
  Not available: `souffle`, Python 3.8 — so Task 3f must go through Docker.

### Next

Tasks 3a and 4a enumeration start once the corpus is re-cloned. Task 2 demo and
Task 5a need the data junction. GPU estimates for Task 2 full-scale and Task 5b
go to the user at Checkpoint B.

## 2026-10-08

**Task 2 (Q-D2), demo tier — run, analysed, provisional until the result files
are committed.** PhysioNet A to B, 900 stays/site, 5 seeds, CPU, `--analyse`
output transcribed from the pod terminal; the five `task2_seed*.json` files are
not yet in the repo, so the ledger rows wait for them.

Mean relative probe-loss reduction versus A0 (r), paired within seed, df 4,
critical t 2.132:

| level | A1 shipped | A2 extra source | A3 joint mask | A4 marginal fill | R | verdict |
|---|---|---|---|---|---|---|
| 5% | 0.0313 (t 3.96) | 0.0096 (t 1.18) | 0.0100 (t 1.10) | 0.0165 (t 1.94) | 0.02 | values-dominated |
| 20% (primary) | 0.0901 (t 12.02) | 0.0436 (t 10.40) | 0.0385 (t 6.82) | 0.0584 (t 10.36) | -0.11 | values-dominated |

- A1 minus A2 clears the critical value at both levels (t 8.18 and 7.67), so R
  is defined at both. A3 minus A2 is not significant (t 0.16 and -1.46).
- **The pre-stated prediction missed.** It was "mixed, leaning values-dominated,
  0.25 < R < 0.6". Observed R is 0.02 and -0.11, below the predicted range, so
  the verdict class agrees with the lean but the magnitude does not. Missingness
  carried less than predicted.
- **Corpus size explains a large share of the 20% effect.** r2 / r1 = 0.48 at
  20% (0.31 at 5%). The pre-registered confound rule is r2 >= 0.5 r1, so the
  result is not "confounded with corpus size", but it clears the line by 0.017.
  The paper must report 0.48, not just the verdict. Target exposure still adds
  beyond volume (A1 minus A2 t 7.67).
- **Joint mask structure does not help; marginal fill might.** A3 is below A2
  at 20% (R negative). A4 is above A2 at 20%. Exploratory and post hoc, not
  pre-registered: A4 minus A2 per-seed t is about 4.5, and A4 minus A3 about 3.6.
  A3's achieved fill (0.22 on the 300-stay smoke test, against a target of 0.30)
  is below the target because the transplant can only remove observations, so A3
  confounds mask structure with extra sparsity. The A3 versus A4 contrast is
  therefore not clean, and the honest statement is that this design cannot
  separate them.
- **Reproducibility.** The CPU rerun reproduces the archived detector 2 numbers
  to six digits: A0 mean 0.0067391 against archived 0.0067391, 5% delta 3.129%
  against 3.129%. The earlier V100 run differed by about 1% (5% delta 4.0%), so
  GPU runs of this check are not bit-comparable with the archive.

Claim-relevant for the paper: detector 2's scope statement does not need
loosening toward "values only" being false, but the 20% effect is roughly half
corpus size, and that belongs in the limitations.

**Task 3a — enumeration done.** Patterns P1-P4 were committed alone as
`b845cc0` (2026-10-08 00:50:04 -0700) before the scan ran. Over the 18 pinned
repos: 688 Python files parsed, **103 candidate sites** (P1 argmax/max 61, P2
best-update 10, P3 early stopping 12, P4 named selectors 20), **53 sampled** at
most 5 per repo with seed 20261006. The cap of 60 was not reached because the
corpus only has 103 sites. Three repos yield no site (mimic-code, retain,
sepsis3-mimic).

Coverage gaps that the paper must carry with any sensitivity figure:
- **126 notebooks were not scanned.** The pinned corpus is notebook-heavy
  (Benchmarking_DL_MIMICIII 43, MIMIC-IV-Data-Pipeline 24, mimic-code 20,
  sepsis3-mimic 13, robustdg 10). Selection logic that lives only in notebook
  cells is invisible to this enumeration, and to the shipped detector, which
  reads `.py` files.
- **8 files did not parse** (retain 3 of 3, Benchmarking_DL_MIMICIII 4,
  robustdg 1), consistent with Python 2 sources. Counted as unparseable, never
  as clean. `retain` has no parsed file at all.
- 47 test-directory files were excluded by rule.

Next is 3b labelling by the committed rubric, done before detector 3 is run on
any sampled file so labels cannot be influenced by its verdicts.

**Task 3b/3c — labelled and run.** Rubric addendum `4c461eb` and labels
`e82be15` (2026-10-08 00:55:44 -0700) were committed before detector 3 was run on
any sampled file. 53 sites: **0 CONTAMINATED, 1 DISCLOSED_ORACLE, 1 AMBIGUOUS,
21 SOUND, 30 NOT_SELECTION.** Only 23 sites are real selections, and they sit in
15 distinct files, so they are not independent.

- **The sensitivity denominator is zero.** k = CONTAMINATED = 0, so sensitivity
  is undefined; it is not "0%". The pre-registered hope that "0/k converts no
  coverage into no sensitivity with a denominator" does not apply: there is no
  k. What the corpus does give is a prevalence statement: undisclosed
  contamination was 0 of 23 real selection sites, Wilson 95% upper bound 0.143.
- **The one disclosed oracle** is robustdg `train.py:303`: `np.max` over
  per-epoch test accuracy, printed as "Final Test Accuracy (Target Validation)".
  The ambiguous site is robustdg `utils.py:357-364`, which selects on a loader
  passed as an argument (`te_dl`) with no caller in the corpus.
- **Detector 3 returned INDETERMINATE on all 53 sites, under both vocabularies**
  (36 distinct files). It issues no clean verdict, so no specificity claim may
  be made, and it did not flag the disclosed oracle. This is the same
  recognition-rate gap the paper already reports, now with a denominator.
- Verdicts are file-level and labels are site-level; reported as a granularity
  mismatch, not corrected.
- **3e is only partly done.** A blind relabel of 20 sites by the same model that
  holds the labels in context cannot be blind, so none was run and no agreement
  figure is claimed. `USER_SPOTCHECK.md` has six randomly drawn sites (seed
  20261008). Five of the six are NOT_SELECTION, so it is weak at testing the
  contaminated category; that is what the draw gave and it was not redrawn.
- Not started: 3f (Yang et al. via Docker, 90-minute gate) and the live
  search for other baselines.

## 2026-10-08 (later)

**Task 5a — run on the CPU pod, provisional until the result files are
committed.** Detector 2 and the three baselines read off the same models: 900
stays/site nominal, 5 seeds, thresholds unchanged. Numbers transcribed from the
pod terminal; the seed files are not in the repo yet, so no ledger rows yet.

| level | detector 2 (paired rel. delta, t) | k-fold instability | train/test gap | external floor |
|---|---|---|---|---|
| 0% | not testable (0% vs itself) | flags 5/5 | flags 4/4 (1 undecidable) | flags 4/5 |
| 5% | -3.1%, t -3.96, flag | 5/5 | 4/4 | 4/5 |
| 20% | -9.0%, t -12.02, flag | 5/5 | 4/4 | 4/5 |
| 100% | -15.6%, t -9.54, flag | 5/5 | 4/4 | 3/5 |

- **The baselines fire at 0% leakage.** FPR is 5/5, 4/4 and 4/5, so on identical
  data they carry no information, the same as the archived 2400-stay result
  (TP 3, FP 1, TN 0). The paper's "fire at every level including 0%" is
  confirmed, now at the same scale as detector 2 and with 5 seeds.
- **Paper claim that needs softening: "leakage does move downstream performance
  in the expected direction".** Change in target AUROC versus 0%: 5% -0.0003
  [-0.0066, +0.0060]; 20% +0.0094 [-0.0113, +0.0302]; 100% +0.0100 [-0.0117,
  +0.0318]. Every interval includes zero and the 5% point estimate is negative.
  The point estimates at 20% and 100% are positive; the data do not establish a
  direction. The paper's gap figures (0.117 to 0.103) came from 3 seeds with no
  interval.
- **Paper claim that needs softening: "an order of magnitude larger".** The
  0% source-to-target AUROC gap is 0.090 [0.039, 0.142] (4 seeds with the
  quantity defined). Signal-to-nuisance ratio, per-seed mean: 5% -0.04
  [-0.16, 0.08]; 20% 0.007 [-0.29, 0.30]; 100% 0.024 [-0.32, 0.37]. Ratios of
  means are -0.02, 0.05, 0.06, so "roughly an order of magnitude" holds for the
  point estimates, but the intervals cannot exclude a ratio as large as 0.37 at
  100%. State the point estimates and the intervals together.
- **Paper claim that needs qualifying: detector 2's "clean 0% control".**
  The shipped detector compares its 0% arm with itself, so the relative delta is
  exactly 0 and it cannot flag; TN=1 is by construction. The exploratory (not
  pre-registered) null replicates retrain the 0% arm with four other
  initialisation/shuffle seeds on the same splits and apply the detector's test
  against the original: 0 of 4 flagged, Clopper-Pearson 95% [0.000, 0.602]. That
  is consistent with no false positives but is weak evidence, and the table's
  "FPR 0.00" should read as 0/4 [0, 0.60] with that provenance.

**Task 4 — enumerated and labelled (4a-4c).** Frozen before use: selection rule
`bc365cf`, S1-S4 patterns `073d042`, rubric `879d885` (01:41:00 -0700, before any
site was read). AIF360 was not previously pinned; it is now pinned at
`34877916b7` (default-branch HEAD at clone time).

- **Selection.** The mechanical rule chose 6 new repositories: ssdg-benchmark,
  NICO-plus, WILDS, TableShift, BasicTS, fairseq2. Two of them are off-topic for
  "fairness toolkit" (a time-series forecasting library and a sequence-modelling
  library): the star-sorted search for that phrase returned only two results and
  both passed the README-paper test. Topic 4 returned four tiny repositories
  none of which had a paper link, and topic 5 returned nothing. Nothing was
  swapped by hand. Task 4 therefore rests on the 19 pinned repositories plus 6
  of mixed relevance.
- **236 candidate sites, 88 sampled** (cap 120 not reached). 126 notebooks are
  still not scanned, as in Task 3.
- **Labels (88): 4 REACHABLE_UNGUARDED, 20 GUARDED, 24 UNREACHABLE, 40
  NOT_APPLICABLE** (3 of those undecidable). REACHABLE_UNGUARDED is 4 of 48
  applicable sites, **8.3%, Wilson 95% [3.3%, 19.6%]**; among verdict or
  selection sites 1 of 27, 3.7% [0.7%, 18.3%].
- **The convention decides the headline.** I treated NaN that arises only when
  training diverges as outside supported use. If it counts, 12 more sites flip
  (comparisons against a best-so-far, `argmin` over losses, early-stopping
  thresholds that a NaN silently fails) and the figure is **16 of 48, 33.3%
  [21.7%, 47.5%]**. Both figures must be reported together; the rubric did not
  settle this in advance and I chose the narrower reading, which lowers the count.
- **The 4 positives** (3 files, 3 repositories; two are one hazard in one file):
  tableshift `college_scorecard.py:170`, where `(target > 0.5).astype(int)`
  turns a NaN target into 0 because the preprocess function runs before the NaN
  drop (reachability inferred from the dataset's `na_values`, not executed);
  fairseq2 `arrow_transform.py:288` and `:306`, where `pc.all` skips nulls so null
  rows pass a length filter; robustdg `utils/scripts/utils.py:579`, where
  `max(loss_tr, loss_te)` returns `loss_tr` when `loss_te` is NaN, defeating the
  `np.isfinite` guard on the next line. Only the last is verdict-type.
- **Pre-stated reading 4e.** The paper claims the pattern is structurally
  present in verdict-rendering code, not common in evaluation code. A low figure
  is consistent with that; the honest statement is 3.7% to 8.3% under the narrow
  convention and up to a third under the broad one, each with its denominator.
- 4d is only partly done: a blind relabel by the same model that holds the labels
  cannot be blind, so none was run. Six more sites are in `USER_SPOTCHECK.md`,
  part 2, for you to label.
- Docker Desktop is not running (CLI present, daemon unreachable), so 3f has not
  started; its 90-minute clock has not begun.

**Task 5a — files in the repo, all numbers match the pod output.** One more fact
from the seed files bears on every AUROC in this section: target prevalence is
1.3% to 3.1%, so the 222-225-stay target probe holds roughly 3 to 7 positive
stays per seed, and in one seed the in-domain AUROC is undefined. A cross-site
AUROC built on a handful of positives cannot resolve a 0.01 change, which is
the plain reason the downstream baselines cannot see this leakage. The paper's
"order of magnitude" sentence should say this instead of implying a measured
separation.

**Task 3f — done (gate: started 02:06, image ready about 02:30, run 02:32).**
Yang et al. built only after three environment changes (base image 20.04,
`--unsafe-perm`, Node 14); the unmodified Dockerfile does not build. Run on both
fixtures it reports 0 in all three categories, identically for the buggy and the
corrected file, and its own relations show it recognised no model pairing at all
in either (ModelPair, TestDataWithModel, TrainingDataWithModel all 0 rows). So it
neither detects the contamination nor separates the two files, and a zero is not
a clean verdict. Full record in `results/task3f_yang.md`. Live search for other
baselines: none found for detector 3 beyond Yang et al., none found for detector 4
in two queries (`results/task3f_search.md`). Two citations verified in
`CITATIONS_VERIFIED.md`.

**Task 6 — done (CPU, local, no model).** Detector 5 unchanged, run on identical
stays and seeds with the original component set and with MAP + HH only.

- **Pre-stated reading resolved: the false negative is instantiation-dependent.**
  Original set, PhysioNet A vs B: composition_gap_ratio 0.277 (n=900) and 0.287
  (n=1500), mean over 5 seeds against the 0.30 gate; variant A flags the flagship
  in **only 3 of 5 seeds** at both sizes (per-seed range 0.17 to 0.40), so even
  the original instantiation is a seed-level coin flip near the gate, not a
  uniform miss. Restricted to MAP + HH the ratio is 0.935 and 0.942 and A flags
  5/5. The paper's sentence "composition ratio is 0.27 against a 0.30 gate, just
  under" is the mean of a quantity that straddles the gate across seeds, and it
  depends on the oxygen term.
- **That does not make the restricted detector validated.** The ratio is a ratio
  of two gaps and is unstable when the naive gap is near zero: on the same-site
  control it averages 2.905 (sd 5.5, range 0.16 to 12.8) at n=900 and 0.336 at
  n=1500, above the gate in both. The controls stay silent (0/5) only because the
  availability ratio is about 1; the flagship is separated from controls by
  availability alone (ratio about 35). This is the "one of two gates is
  decorative" finding again, now on PhysioNet as well as at full scale.
- **External, five seeds, detector unchanged.** Original set: variant A flags 1/5,
  4/5, 4/5 at 50/80/95% HCO3 ablation, variant B 1/5, 5/5, 5/5; controls 0/5.
  Restricted: A and B both 1/5, 5/5, 5/5; controls 0/5. The detection floor is
  between 50% and 80% either way. The restricted composition ratio separates
  ablation from control here (80%: 0.70 to 4.48 against control 0.09 to 0.56). The
  committed `detectors/results/external5.json` records variant A silent at every
  level, which is the single-seed run noted before; the five-seed rerun above
  supersedes it and the paper's external A figures should be checked against it.
- Undecidable: 0 in every cell. At 95% ablation HH is absent from one side in 4 of
  5 seeds, which sends the availability ratio to infinity by construction.

**Task 5c — done (existing artifacts only).** The standard check for detector 1 is
the cross-site prevalence ratio. With five definitions per site there are 25
cross-site pairs: 8 are labeller mismatches (ICD at one site, SOFA at the other)
and 17 use the same construct at both sites. The mismatch pairs have |log
prevalence ratio| 0.83 to 1.34. The same-construct pairs run from 0.34 (ICD at both)
to 2.25, and SOFA at both sites gives about 1.4 to 2.3, because MIMIC-IV demo
prevalence (0.52 to 0.56) is about six times eICU's (0.06 to 0.09). A
flag-on-large-ratio rule therefore flags the legitimate SOFA-vs-SOFA comparisons
more strongly than the real mismatches: AUROC 0.059 for picking mismatches, i.e.
inverted, not merely uninformative. Descriptive only (8 against 17 pairs built
from 10 prevalences, demo cohorts of 117 and 1627 stays). Full-scale values are
MISSING. The archived `prevalence_ratio` field in `external1.json` is a split-half
within-site quantity and was not used.

**Task 5e — paragraph written** (`results/task5e_detector5_scope.md`).
**Task 4f — done**, output in `results/task4f_demo_output.txt`. On the verbatim
fragments, a NaN record listed first wins the `max(..., key=...)`, a NaN listed
later is ignored, an empty list raises, and both a NaN value and an empty list
pass the `any([v==-1 ...])` guard (the empty list yields NaN through 0/0). The
script states that this is the semantics of the pattern, not a bug in shipped
DomainBed; whether callers can produce these inputs was not traced.

## 2026-10-09

**Addendum 2 committed first** (`d14687a`, 2026-10-09 11:43:38 -0700), before any of
the analyses below: Task 4 reporting, the 20-replicate detector 2 null, 5a-prime,
the detector 5 per-seed archive, spot-check reporting.

**Task 4 reporting, both conventions, exact intervals (strategy decision 1).** The
NaN convention was not fixed in advance; the narrow reading was applied while
labelling. Neither is chosen. Headline pair: **4 of 48 (CP95 [0.023, 0.200]) and
16 of 48 ([0.204, 0.484])** applicable sites. Split by site kind:

| reading | verdict/selection | other | Fisher two-sided p |
|---|---|---|---|
| narrow | 1/27 [0.001, 0.190] | 3/21 [0.030, 0.363] | 0.306 |
| broad | 11/27 [0.224, 0.612] | 5/21 [0.082, 0.472] | 0.355 |

The strategy agent's hand figure (1/27 against 3/21, p about 0.3) is confirmed:
exact p = 0.3055, matching `scipy.stats.fisher_exact`. Neither split is
significant, so the data do not show verdict/selection code to be more or less
exposed than other evaluation code. The four narrow-reading positives:
- tableshift `tableshift/datasets/college_scorecard.py:170` @ `fca9429814` (other)
- fairseq2 `src/fairseq2/data/parquet/arrow_transform.py:288` @ `7f06d6f4f5` (other)
- fairseq2 `src/fairseq2/data/parquet/arrow_transform.py:306` @ `7f06d6f4f5` (other)
- robustdg `utils/scripts/utils.py:579` @ `3eee1730ae` (verdict/selection)

(Four sites in three files; the earlier report counted files, not sites.) These
intervals are exact Clopper-Pearson and replace the Wilson figures used on
2026-10-08.

**Detector 5 per-seed archive and Type 2 check (addendum 2, section D) — done.**
- The strategy agent's hand estimates are confirmed. From the archived summary
  statistics, P(flag) = Phi((mean - 0.30) / sd) = **0.418** at n = 1200 (mean 0.283,
  sd 0.082; observed 2/5) and **0.235** at n = 4000 (mean 0.274, sd 0.036; observed
  0/3).
- Re-running the shipped procedure reproduces the n = 1200 archive exactly
  (per-seed 0.270, 0.289, 0.345, 0.152, 0.358; the two seeds above 0.30 are the
  two flags) and the first three n = 4000 seeds (0.2328, 0.2909, 0.2986). Two
  further n = 4000 seeds (0.255, 0.281) give mean 0.272, sd 0.027, **P(flag) =
  0.148, observed 0/5**, CP95 [0, 0.52]. The availability ratio is 28 to 62 in
  every run, so the conjunction reduces to the composition gate.
- At the Task 6 sizes the same model gives 0.411 (n = 900) and 0.435 (n = 1500),
  observed 3/5 at both.
- **Reconciliation, one sentence.** The 3 of 5 (Task 6, n = 900 and 1500) and the 2
  of 5 (n = 1200) are different five-seed samples from one process whose predicted
  per-seed flag probability is about 0.42, so a one-seed difference is ordinary
  binomial variation (Fisher exact p = 1.0 for 3/5 against 2/5; P(3 or more of 5)
  = 0.35 at p = 0.42).
- **`detectors/results/external5.json` replaced** by the unchanged five-seed
  runner (old one-seed file stays in git history). Variant A: TP 9, FP 0, FN 6,
  TN 10, i.e. precision 9/9 and FPR 0/10; flag rates 0.2, 0.8, 0.8 at 50/80/95%
  ablation (B: 0.2, 1.0, 1.0); both controls 0/5. It agrees exactly with Task 6's
  full-component external numbers.

**Detector 2 null with 20 replicates (addendum 2 B, exploratory) — done.**
**1 of 20 replicates flagged, Clopper-Pearson 95% [0.001, 0.249].** The pre-stated
reading (3 or fewer of 20 is consistent with 5%) is met. Two cautions, neither
changes the reading: (i) three of the 20 replicates have |t| above 2.132 (one
flagged, one negative but not all five deltas negative, one in the opposite
direction); three or more of 20 at a nominal 5% has probability 0.075, so the
paired t may be mildly anti-conservative in a two-sided sense; (ii) the null
uses independent model seeds for the two arms, whereas detector 2's own arms
share a model seed within a draw, so the per-draw noise in the null (sd of the
relative difference 0.070) is larger than in the real comparison. This replaces
"FPR 0.00 by construction" with an observed 1/20 on a harder null.

**5a-prime (addendum 2 C, exploratory) — done.** The full held-out target site has
13,879 to 13,888 stays and 285 to 289 positives per seed (about 2.1%), against the
3 to 7 positives of the 5a probe. Change in target AUROC versus 0%: **+0.0007
[-0.0010, +0.0025] at 5%; +0.0027 [-0.0009, +0.0062] at 20%; +0.0037 [+0.00003,
+0.0074] at 100%.** By the pre-stated reading a direction is established only at
100% leakage (interval excludes zero by a hair, all five seeds positive), not at
5% or 20%, and the effect is about 0.004 AUROC. The 0% in-domain minus
full-target gap is 0.142 [0.029, 0.254], so the leakage effect is about 2.6% of
the nuisance gap at 100% (0.5% at 5%, 1.9% at 20%): the "order of magnitude"
statement holds with room to spare, and it can now be said with a properly
sized target. The paper's "moves downstream performance in the expected
direction" should read: detectable only at 100% leakage, by about 0.004 AUROC.
Identity check against the committed 5a files: probe loss differs by at most
3.2e-8, probe AUROC by at most 0.0015, in-domain AUROC by 0.0011; the 5a run was
on torch 2.14.1 / numpy 2.5.3 and this one on 2.13.0 / 2.4.3, so the models are
numerically the same but the downstream logistic fit is not bit-identical.

**Full-scale detector 1 labels regenerated (the job completed 2026-10-09 13:22; its
stdout and the saved label arrays were lost with a scratch clean-up, the aggregate
JSON survives).** Unchanged `run_external1.py` on the full MIMIC-IV (74,829 stays)
and eICU-CRD (132,900 stays) data, audit draw of 500 at audit seed 0. The kappa on
that one audit draw: MIMIC SOFA window vs single-point 0.634 (the whole-cohort value
the paper quotes is 0.602), eICU 0.869; ICD vs SOFA is flagged in both (0.204 and
0.514). The run wrote over the demo `detectors/results/external1.json` in the working
tree; the full-scale copy is saved as `rebuttal/results/full_scale_external1.json` and
the demo file is restored to its committed content. This file has per-draw kappa and
whole-cohort prevalences only: the whole-cohort kappa, the cohort bootstrap and the
control dispersions still need the label arrays, which have to be regenerated
(about 1.6 hours) and this time kept outside the scratch folder.
