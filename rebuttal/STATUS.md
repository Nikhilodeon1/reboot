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
