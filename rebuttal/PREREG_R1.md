# Pre-registration — rebuttal round 1 (ML4H 2026, submission 381)

Written and committed **before** any rebuttal code or run. Tasks 2–6 below fix
arms, metrics, decision rules and the reading of every outcome in advance. This
is the paper's own Type 4 rule applied to its own rebuttal.

Freeze: 2026-10-10 12:00 PT. Author response closes 2026-10-12 23:59 AoE.

## 0. Scope and standing rules

- **No detector edits.** Detectors 1–5, their thresholds, gates and vocabularies
  are frozen. Every variant is a separate labelled arm. A detector bug stops
  work and is reported, not fixed silently.
- **Undecidable is not clean.** Every check returns a decidability flag.
  Undecidable cases get their own column. Absent uncertainty renders `MISSING`.
- **Scale labels** on every number: demo/full, n stays, n seeds, data pair.
- **Seeds** ≥ 5 for anything stochastic; data splits resampled per seed, not
  only model seeds. Paired tests use df = seeds − 1 (5 seeds → df 4, one-sided
  5% critical value 2.132).
- **DUA**: aggregates only under `rebuttal/`. No per-stay or per-patient files.
- **Anonymity**: no names, institutions, home paths, session UUIDs or emails in
  any committed file or log.
- Unfavourable results are recorded at equal prominence; anything that changes a
  claim in the paper is reported to the user the same day.

### Deviations from the task prompt, fixed here in advance

| # | Prompt says | We do | Why |
|---|---|---|---|
| D1 | deliverables under `chat1_protocol/rebuttal/` | `rebuttal/` at the repo root | the repo was split; the former `chat1_protocol/` **is** this repo root |
| D2 | leak size L = 5%/20% **of the source set** | L = 5%/20% **of the target leak pool** | standing rule 1 says match the detector's own convention. `check2_pretrain_leakage.run_one` computes `n_leak = round(frac * len(leak_ds))` over the *leak pool*. Using the prompt's definition would make Task 2 arms incomparable with every published detector 2 number |
| D3 | A2 "skip if the detector replaces rather than adds" | A2 runs | verified: `train = ConcatDataset([src_ds, Subset(leak_ds, idx)])` — the detector **adds** |

## 1. Confirmed before writing this document

| Fact | Status |
|---|---|
| `load_physionet2019(..., keep_raw=True)` returns per-stay `raw_ts` | confirmed — A3/A4 can transplant masks pre-normalization |
| detector 2 adds leak stays to the corpus | confirmed |
| GitHub API reachable | confirmed (HTTP 200) |
| Docker available; no `souffle`, no Python 3.8 on PATH | confirmed — Task 3f must go through Docker |
| 18-repo scan corpus clones | absent; must be re-cloned at the SHAs pinned in `detectors/external/SCAN_CORPUS.md` |
| `data/` junction | absent; must be recreated before any data-touching task |

## 2. Task 2 — detector 2: values vs missingness (Q-D2)

**Question.** Does detector 2's probe-loss drop come from target *values*, target
*missingness*, or corpus *size*?

**Arms** (per seed; identical probe slice, source set, hyperparameters; L at 5%
and 20% of the leak pool, matching the detector's convention, D2 above):

| Arm | Content |
|---|---|
| A0 | no leak |
| A1 | L target stays (values + target missingness) — the shipped detector |
| A2 | L extra **source** stays, unmodified (corpus-size control) |
| A3 | L extra source stays, each wearing the observation mask of a distinct random target stay, applied to `raw_ts` before normalization and forward-fill, then identical preprocessing |
| A4 | L extra source stays, randomly masked to match the target's **per-variable fill proportions** |

A2–A4 stays are drawn from a source hold-out pool disjoint from the source
training set, reserved before any arm runs. The probe slice never changes.

**Metric.** r_k = mean paired within-seed relative probe-loss reduction vs A0
(positive = improvement). Primary level 20%, secondary 5%. Report per-arm
mean ± SD and the paired t against A0 with df 4.

**Decision rules** (fixed now):

- r2 ≥ 0.5·r1 → detector 2's effect is **confounded with corpus size**. Reported
  as a new limitation; the detector is not changed.
- Missingness share R = (r3 − r2) / (r1 − r2), computed **only if** (r1 − r2)
  clears the one-sided critical value; otherwise `undetermined`.
- Values-dominated: R ≤ 0.25 and (r3 − r2) not significant.
- Missingness-dominated: R ≥ 0.75 and (r1 − r3) not significant.
- Otherwise mixed.
- A3 vs A4 separates marginal per-variable fill (A4) from joint mask structure
  (A3).

**Pre-stated prediction.** We expect **mixed, leaning values-dominated**
(0.25 < R < 0.6). Reason: the fill audit shows training fill moves only
0.588 → 0.539 across the whole 0→100% range, a small perturbation relative to
the probe-loss effect, so missingness alone is unlikely to carry it. If R ≥ 0.75
the paper's scope statement was too generous to the detector and we say so.

**Scale.** Demo PhysioNet A→B, 900 stays/site, 5 seeds — mandatory (Tier 1).
Full-scale MIMIC-IV→eICU is Tier 2, GPU, gated on a written cost estimate and
the user's go; it needs a 10% source hold-out and an A0 rerun on the reduced
source for comparability.

**Stopping.** If the demo arms cannot be built (e.g. insufficient disjoint
source stays for L at 20%), report the shortfall and run 5% only.

## 3. Task 3 — detector 3 sensitivity with a denominator (Q-D3)

**3a enumeration.** Over the 18 pinned repos, collect candidate selection sites
mechanically: `argmax/argmin/max/min` with a key over metric collections;
`if metric > best` followed by save/assignment; early stopping on a monitored
metric; functions named `select|best|sweep|tune|hparam`. Patterns are committed
before the scan. Counts per repo recorded before any labelling. Sample ≤ 5 sites
per repo at a recorded seed; cap 60 sites or 3 hours.

**3b rubric** (committed before labelling). Per site record SELECTION_SPLIT and
REPORTED_SPLIT from {train, source validation, held-out target, OOD target,
test, unknown}, with file, line range and SHA as evidence.

- CONTAMINATED: the same held-out/OOD/test split is used both for selection and
  for the number presented as held-out or zero-shot.
- DISCLOSED_ORACLE: authors label it as such; contaminated by construction.
- AMBIGUOUS: config-dependent; counted separately, never folded into either.

**3c.** Detector 3 run unchanged on each sampled site's file: shipped vocabulary,
and the fitted-extended vocabulary as a second column. Verdicts flag / clean /
indeterminate.

**3d reporting.** n sites, k contaminated, a ambiguous, sensitivity = flags among
contaminated / k with Wilson 95% CI, indeterminate count. **No specificity claim
unless the detector issues clean verdicts.** 0/k is a publishable result: it
converts "no coverage" into "no sensitivity, with a denominator".

**3e verification.** Blind relabel of 20 random sites in a fresh pass; report
percent agreement. Six randomly chosen sites go to `USER_SPOTCHECK.md` for the
user to label independently; agreement reported.

**3f Yang et al. baseline.** Yang, Brower-Sinning, Lewis, Kästner, *Data Leakage
in Notebooks: Static Detection and Better Processes* (ASE 2022), tool
`github.com/malusamayo/leakage-analysis`. Multi-test leakage — reusing test data
for model selection — is adjacent to detector 3's confound and the paper does
not cite it. **Gate: 90 minutes** to a working invocation via Docker. Run on both
detector 3 fixtures (buggy and corrected). Record output verbatim, including
"could not parse" or "reports nothing". If it will not run, record the exact
failure and cite only. Also run a live search for other model-selection-leakage
tools and for anything applicable to detector 4's circular-derived-variable
problem; record query, date, result. Novelty claims may not exceed what the
search supports.

## 4. Task 4 — Type 1 falsy-as-clean beyond three repos (Q-EXT)

**4a corpus.** The 18 pinned repos + AIF360 + up to 10 new repos chosen by a rule
fixed **now**, before any file is read: for each of five topics — domain
generalization benchmark, distribution shift benchmark, fairness toolkit,
hyperparameter/model-selection benchmark, calibration/uncertainty evaluation
library — take the top 2 GitHub results by stars that are Python, have an
associated paper, and are not already included. Query, timestamp, ranks and
pinned SHAs recorded. No hand-picking. If GitHub becomes unreachable, the
subtask stops and says so.

**4b sites** (patterns committed first): S1 selection by
`max/min/argmax/argmin/sorted`-first over metric collections; S2 threshold
comparisons on metric-like names; S3 `any()`/`all()` guards over comparisons
against a sentinel or over possibly-empty lists; S4 aggregation whose key set
comes from the first run or element.

**4c labels.** GUARDED (an explicit nan/None/empty check dominates the site),
UNREACHABLE (degenerate input excluded by construction or shipped config),
REACHABLE_UNGUARDED (degenerate input possible under supported use **and** the
falsy collision changes the output), NOT_APPLICABLE. Report per-repo and overall
counts, the REACHABLE_UNGUARDED proportion with a Wilson CI, and every positive
with file, line, SHA. Repos searched with nothing found stay in the table.

**4d verification.** Blind relabel of 25% of sites, percent agreement; 6 sites to
`USER_SPOTCHECK.md`.

**4e pre-stated reading.** The paper claims the pattern is structurally present
in *verdict-rendering* code, not that it is common in evaluation code generally.
A **low** REACHABLE_UNGUARDED proportion is consistent with that claim; a **high**
one strengthens it. Either way the number is reported with its denominator, and
neither outcome is presented as a surprise after the fact.

**4f consequence demo (Tier 3).** Copy the verbatim two or three lines of
DomainBed's bare `argmax` and the `any([v == -1 ...])` guard into a standalone
script, citing file, line and SHA; confirm by inspection that they are pure; run
on synthetic inputs (NaN first vs NaN later; empty list). No repo import, no I/O,
no network. The output states that this demonstrates the semantics of the
verbatim pattern, **not** a bug in shipped DomainBed.

## 5. Task 5 — baselines (Q-BASE)

**5a head-to-head, demo scale (Tier 1).** The published baselines ran at 2400
stays/site and detector 2 at 900, so they were never on the same data. Rerun
detector 2 and all three baselines (external floor, k-fold instability,
train/test gap) on identical stays, identical leakage levels, identical 5 seeds,
thresholds unchanged. Report per-level results with intervals, FPR, undecidable
counts, and the signal-to-nuisance ratio (leakage-induced AUROC change ÷ the 0%
source-to-target gap) with seed intervals.

**5b full-scale same-pair (Tier 2, GPU, gated).** Detector 2's full-scale
MIMIC-IV→eICU protocol and seeds. Downstream: frozen encoder, regularized
logistic head. Label: Sepsis-3 if the cached labels survive; **otherwise
hospital mortality**, whose definition is identical in both databases — a
documented deviation, declared here in advance. One seed at one level runs
first; cost and time are extrapolated and sent to the user; no further runs
without a go. If it cannot fit the $8 cap, 5a stands alone and the response
concedes the scale gap explicitly.

**5c detector 1 baseline (Tier 2, CPU).** Standard practice compares outcome
prevalence across sites. Pre-registered statistic: **log prevalence ratio**.
Show it cannot separate a labeller mismatch from genuine case-mix shift:
prevalence under identical definitions across sites vs under mismatched
definitions, from existing artifacts and demo-scale labels. Full-scale values
marked MISSING if the label arrays are gone.

**5d detectors 3 and 4.** Yang et al. (3f) is detector 3's baseline. For
detector 4, report the live-search outcome; no baseline will be invented.

**5e detector 5.** Out of scope, with the reason stated in one paragraph: the
naive cross-site gap is the quantity detector 5 decomposes, so it is not an
independent check. Not run unless everything else is finished.

## 6. Task 6 — detector 5 common-component sensitivity (Q-D5)

Sensitivity analysis only; the detector's definition does not change. MAP and
Henderson-Hasselbalch are present in every database; Severinghaus is circular on
PhysioNet (PaO2 is reconstructed from saturation) and SaO2 is absent externally.

Rerun detector 5 restricted to {MAP, HH} on the PhysioNet A vs B flagship case,
on the external ablation cases (50%, 80%, 95%) and on both controls, 5 seeds.
Report `composition_gap_ratio`, availability ratio, flags, undecidable counts
(HH coverage is low externally, so undecidable may dominate — that is a result).

**Pre-stated reading.** Still under the 0.30 gate → the false negative is **not**
an artifact of the analogous component set. Over 0.30 → it **is**
instantiation-dependent, and the paper's framing of detector 5's false negative
must be qualified. Whichever happens is reported.

## 7. Task 1 — statistics already determined (Q-STAT, Q-DEF)

Fixed before computation:

- **Intervals.** Clopper-Pearson 95% for every confusion-matrix proportion, per
  detector and pooled. The pooled figure is labelled *reference only,
  heterogeneous cases* wherever it appears.
- **Control margin.** m = |threshold − control statistic| ÷ SD of that statistic
  at the operating audit size, from saved bootstrap draws or per-seed values.
  **Discriminating iff m ≤ 3; ceiling iff m > 3.** This rule is fixed now and
  will not be tuned afterwards. Where draws were not archived, the margin is
  reported in native units and the z value marked MISSING.
- **Type 2 model.** P(flag) ≈ Φ((τ − θ\*) / σ_audit), θ\* the whole-cohort κ,
  σ_audit the SD of κ over 500-patient audit draws. Predicted vs observed table
  for every detector 1 control. We also report how κ for the *same pair of
  legitimate implementations* varies across databases and window variants, since
  the Type 2 claim should rest on that legitimate-variation band rather than on
  "more data cannot help".
- **Validation-depth matrix.** Per detector: positives, controls (internal and
  external), discriminating controls by the margin rule, external ground-truth
  source, scale, seeds, uncertainty type, baseline coverage, manual-label
  coverage. MISSING where absent.

## 8. Gating, ordering and what gets dropped

Priority, never dropped: Task 0, Task 1, Task 2 demo, Task 3, Task 5a.
Drop order if late: Tier 3 (incl. 4f and linters), 5c, Task 6, Task 2
full-scale, 5b, the 10 new repos in 4a (the 19 pinned ones stay).

GPU work requires a written cost/time estimate and the user's explicit go.
Hard cap $8 for this phase. Any long run gets `--save-*` flags, writes to the
persistent volume, and has its resume command committed before launch.

## 9. What each task reports if it is gated off

| Task | If not run |
|---|---|
| 2 full-scale | demo result stands; response states the scale gap and that the full-scale arm was costed and not run |
| 3f | the citation is added and the tool is described as not executed, with the exact failure |
| 4a new repos | the 19 pinned repos carry the result; the sampling rule is still reported |
| 5b | 5a stands; the response concedes the scale gap rather than implying parity |
| 5c, 6, Tier 3 | named in STATUS.md as costed, not run, with the reason |
