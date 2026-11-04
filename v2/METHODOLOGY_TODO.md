# v2 methodology plan (TMLR submission)

Status of this file: a plan. Nothing here is a result until it has a row in `v2/LEDGER_V2.md`.
Standing rules from round 1 still apply: no detector edits (a bug is reported, not fixed); aggregate
outputs only; anonymity; explicit paths when staging; third-party code is run only where a pre-registered
task says so and only inside a container; every experiment is pre-registered by commit order before it runs.

## 0. What the first round left open (from the reviews and our own runs)

1. The evidence is five detectors written by the authors. Types 2 to 4 have no external instance.
2. Detector 2's effect is confounded with corpus size at full scale, and the shipped 0% control cannot show it.
3. Several statements are "consistent with" a model fitted on the same draws, not predictions.
4. The labelling behind the external evidence (53 and 88 sites) rests on one rater plus an LLM check, with 8 of 12
   agreement on the spot-check.
5. The missingness arms of detector 2 exist only at demonstration scale; n = 5 seeds per cell almost everywhere.
6. The paper never shows that following its own protocol repairs a diagnostic.

## 0b. The program chairs' decision (Reject, 26 Oct 2026) and what it asks for

The meta-review credits the problem setup and the transparent negative results, and gives four concerns:
(1) pooled performance figures summarise a small internal suite; (2) evidence across the four failure modes is uneven;
(3) several detectors have substantial limitations; (4) broader significance is not demonstrated: most failures concern
the authors' own tools, with little evidence that the issues affect conclusions in external studies. It adds that the
rebuttal's new analyses were "described largely qualitatively" and that two reviewers kept outstanding concerns.

Consequences for v2:
- Concern 4 is the decisive one. The paper needs executed evidence that a diagnostic failure changes a conclusion in
  work that is not ours. That is the new item E12 and it moves E1 and E2 up. Without it the paper stays "a critique of
  our own tools".
- Concern 1: drop the pooled precision and recall entirely (not "reference only"). Per-detector counts only, in a table.
- Concern 2: state the evidence per type in the abstract and in one table, and add external evidence for Types 2 and 3.
- Concern 3: present the five detectors as case studies of the failure modes, not as the contribution.
- "Described qualitatively": every new analysis appears as a table or figure with its numbers in the paper itself, since
  the readers will not open the repository.

## 1. Experiments, in priority order

Each item: question, design, what it buys, cost, where it runs. "Prereg first" means a committed section in
`v2/PREREG_V2.md` (or an addendum) before any run.

### P0 (cheap, high value, runnable now)

**E3. Detector 1: flag probability against audit size (out-of-sample test of the Type 2 model).**
Question: does the model P(flag) = Phi((tau - theta*)/sigma_n) predict the flag rate at audit sizes it was not fitted on?
Design: full-scale labels, cases MIMIC control (about 0.5), eICU positive (near 1), eICU control (near 0); n in
{100, 200, 500, 1000, 2000, 5000}; 2000 audit draws per cell; sigma_n scaled from sigma_500 with a
finite-population correction; reading rule fixed in advance. Also reports the audit size at which the verdict
would become deterministic (derived; it exceeds the cohort for the MIMIC control).
Buys: Figure 2 with a model curve and observed points; turns the 0.475-vs-0.484 consistency check into a test.
Cost: minutes on CPU, local (per-stay labels stay on this machine).

**E4. Detector 5: fresh-seed test of the Type 2 prediction.**
Question: do 20 fresh seeds flag at the rates the first five seeds predicted (0.417 at n = 1200, 0.148 at n = 4000)?
Design: seeds 5 to 24, shipped `run(seed, n)` unchanged, predictions fixed in advance, Clopper-Pearson interval on the
observed count, same-site control recorded per seed.
Buys: replaces "consistent with, n = 5" with a real prediction; also gives the control's false-positive rate with a
denominator of 20. Cost: about 2 minutes per seed at n = 1200 (more at 4000), parallel on CPU or a pod; open
PhysioNet data only.

**E7. Independent human second rater on every external label (88 Type 1 sites, 53 detector 3 sites).**
Design: blinded sheets generated from the frozen rubrics; a human who has not seen our labels codes all sites
independently; report Cohen's kappa per rubric with an exact interval; disagreements adjudicated by a third
reader and listed. The LLM check stays as a labelled non-independent check.
Buys: the weakest link in the external evidence (8 of 12). Cost: 3 to 4 hours of a person. I generate the sheets.

**E8. Responsible disclosure (action, not an experiment).**
Notify the maintainers of the 3 files with Type 1 positives (tableshift, fairseq2, robustdg) and of any
positives from E1. Drafts are in `v2/DISCLOSURE_DRAFTS.md` (to write). Do it from a channel that does not appear in
the anonymous submission, before submission.

### P1 (extends the case beyond our own detectors; needs an addendum first)

**E1. Executed fuzz test of public checkers on degenerate inputs (Type 1a, external, executed).**
Question: when a public data or model checker is given an input on which its statistic is undefined (all-NaN column,
empty table, single-class labels, constant column), does it say pass, fail, error, or undecidable?
Design: a frozen list of checkers (pinned versions, installed in a container with no network after install),
a frozen list of degenerate inputs, and a rubric that separates documented vacuity from an undocumented pass.
Outcome counts per checker with exact intervals; positives go to disclosure.
Buys: turns the static read of 25 repositories into an executed, reproducible measurement, and it is what a
general reader will care about. Cost: a day; Docker locally; no clinical data. Needs your go-ahead to install
the pinned packages.

**E2. Type 2 on public thresholds (external, public data).**
Question: how often is a widely used pass/fail threshold within 1 to 3 audit standard deviations of the population
value of its statistic at realistic audit sizes?
Design: frozen set of (public dataset, statistic, threshold) cases, for example the four-fifths disparate-impact rule
on Adult, COMPAS and a fixed list of ACS tasks and states, and kappa 0.6 on public annotation sets; population value,
audit-size standard deviation, margin m, flag probability; one table.
Buys: first external Type 2 instances. Cost: hours on CPU; public data downloads need your approval per file.

**E5. Detector 2 v2 with a volume-matched control (a repair under the protocol).**
Design: v2 reports the paired statistic A1 against A2 (leak versus extra source stays), so corpus size cancels.
v1 stays in the paper unchanged. Pre-registered at demonstration scale: a 20-replicate null for A2 against A2',
a dose sweep (1, 2, 5, 10, 20 percent), and the margin of the 0% control.
Buys: a positive result that follows from the protocol: the repaired diagnostic has a discriminating control, a null
rate with an interval, and a stated detection floor. Cost: demonstration scale is CPU or pod; full scale repeats the
earlier local tier (hours). Because it changes a detector, it is a new version with its own pre-registration; it must
not overwrite v1 or move any v1 threshold (that would be Type 4).

**E12. Consequence studies in external work (answers concern 4 directly).**
Question: for the Type 1 positives we found in other people's code, and for a Type 2 threshold in a public audit, does the
failure change a number or a conclusion that a user of that code would report?
Design: for each of the four reachable and unguarded sites (tableshift college_scorecard, fairseq2 arrow_transform x2,
robustdg utils) construct the realistic input the code is meant for (public data where it exists), run the shipped
function inside a container, and record the output with and without the guard the code lacks; report the affected
fraction of rows or the change in the headline statistic. For Type 2, take published or tool-default pass/fail rules on
public data (E2) and report how often the verdict flips between audit draws or between two accepted operationalizations.
Reading rule per site: no effect, effect on data but not on a conclusion, or effect on a conclusion. A null result is
reported as such. Needs an addendum with the frozen input for each site before any run, and your approval to fetch
any public dataset used.
Buys: the only evidence that speaks to "does this matter outside our tools". Cost: one to three days; Docker; public data.

### P2 (worth doing if time allows)

**E6. Mutation test of the controls.** Seeded mutants of detector 1's statistic and decision rule (run on copies in a
harness, repository files untouched). For each mutant, which controls change verdict? Tests whether the margin rule
predicts which controls can catch a defect.
**E9. Full-scale missingness arms for detector 2.** Needs the raw pre-forward-fill series from MIMIC-IV and eICU-CRD
on the local machine; new loader code under `v2/`, detector untouched.
**E10. More seeds at full scale.** Ten seeds for the full-scale tier would tighten the t-based intervals (df 4 now).
**E11. Type 3 and Type 4 as literature-supported hazards.** No external measurement is possible for Type 4; the
paper states that and cites verified sources for record-level versus subject-level splitting and for analytic
flexibility.

## 2. Writing and housekeeping items

- A running evidence ledger for v2 (`v2/LEDGER_V2.md`) that extends the round-1 ledger. No number enters the paper
  without a row.
- Reconcile the test counts in the reproduction appendix: the clean-up commit deleted `detectors/tests/test_log_phrasing.py`.
  Rerun the suite, report the actual counts, and say so if a test was removed.
- Restore a mirror-ready evidence tree (pre-registrations, rubrics, results, scripts) for the new anonymous
  repository; keep internal strategy documents out.
- Obtain `tmlr.sty` and `tmlr.bst` (the official style files); the draft compiles without them using a fallback.
- Verify every citation (VERIFIED, METADATA-ONLY or removed) and keep `v2/CITATIONS_V2.md`.
- State in the paper that an LLM assisted drafting and checking, per the venue's current policy; the authors
  read and rewrite every section and own every number.
- AUROC-change intervals are t-intervals over 5 seeds; proportions are exact Clopper-Pearson. Name both in the paper,
  by estimand.

## 3. What would change the plan

- If E3 fails (the model misses the observed flag rate at n of 250 or more), Type 2 is described as a threshold-position
  problem with no predictive model.
- If E4 fails, the detector 5 sentence becomes "the ratio straddles its gate"; the model is dropped from the paper.
- If E7 shows kappa below 0.6 on either rubric, the external prevalence figures are reported as rubric-dependent and
  the headline becomes the range across raters.
- If E1 finds no vacuous pass in any checker, Type 1 stays an internal and structural finding and the paper says so.

## 4. Status log

- 2026-11-03: PREREG_V2 section 1 committed (829a11c). E3 run: supported in all three cases (D = 0.026, 0.010, 0.004);
  the MIMIC-IV control's flag rate falls only from 0.492 (n = 100) to 0.411 (n = 5000); model n* = 62,500 of 74,829.
- 2026-11-03: E4 running (seeds 5 to 24). At n = 1200: 13 of 20 flagged (exact 95% interval 0.408 to 0.846), prediction 0.417
  inside the interval by the registered rule, but the fresh ratios have mean 0.341 and SD 0.145 against 0.283 and 0.082 from
  the first five seeds, so five seeds do not pin the model's parameters. n = 4000 still running.
- 2026-11-03: E7 rating sheets generated (blinded): `work_reboot/e7/rater_sheet_3b.md` (53 sites) and `rater_sheet_4c.md`
  (88 sites), with neutral keys. Needs one human rater who has not seen our labels.
- Needs your approval before they can start: E1 (install pinned checker packages inside a container), E2 and E12 (download
  public datasets, name each file and size when asked), the TMLR style files, and any pod use for E5 beyond open data.
- Repository clean-up note: the AST comparison showed no semantic code change between the round-1 commit and HEAD (71 files
  identical after removing comments and docstrings; 21 deleted files are scripts, docs and one test, now kept under
  `v2/evidence_r1`). `detectors/PREREGISTRATION_OUTCOME.md` and `detectors/TODO.md` were deleted from the tree and must be
  restored for the release because the paper cites the outcome document.
