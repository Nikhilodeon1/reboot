# Rebuttal program: progress report for the strategy agent

Written 2026-10-08, after the first rebuttal prompt ("Code Agent Prompt 1 of 2:
rebuttal experiments and methodology") was executed. Freeze is 2026-10-10 12:00
PT; the response is due the evening of 2026-10-11. Everything below is in the
repository under `rebuttal/`; `LEDGER.md` lists every quotable number with its
source file, command and commit, and `STATUS.md` has the dated log.

## 1. Bottom line

All pre-registered tasks that fit the compute rule have been run. Task 2 and 5b
full-scale (GPU) were dropped, as the priority list allows, and the response
should concede that scale gap in so many words. **The results are mostly
unfavourable to the paper's current wording.** Seven claims in the paper need to
change or be qualified (section 3), and one of them is in the abstract. Two
decisions need the strategy agent (section 5).

## 2. Task status

| Task | Status | One-line result |
|---|---|---|
| 0 Pre-registration | done | `25fc617`, 2026-10-06 09:06, before any rebuttal code. Frozen patterns and rubrics for 3, 4 committed before their scans/labels (`b845cc0`, `4c461eb`, `bc365cf`, `073d042`, `879d885`). |
| 1 Statistics | done | Clopper-Pearson intervals; only one detector 1 control is discriminating by the pre-registered margin rule, and it is the coin-flip one. |
| 2 Detector 2, values vs missingness | demo done (5 seeds, CPU) | Values-dominated at 5% and 20% (R = 0.02, -0.11). Prediction missed (we said mixed, 0.25 < R < 0.6). Corpus size explains 48% of the 20% effect. Full scale (GPU) dropped. |
| 3 Detector 3 sensitivity | done | 53 sites: 0 contaminated, 1 disclosed oracle, 1 ambiguous, 21 sound, 30 not a selection. Sensitivity is undefined (k = 0). Detector returns indeterminate on 53 of 53. |
| 3f Yang et al. baseline | done (gate 90 min, used about 30) | Built after three environment fixes, ran on both fixtures: reports 0 on both, recognises no train/test model pairing. |
| 4 Type 1 beyond three repos | enumerated and labelled | 88 sites over 25 repos. REACHABLE_UNGUARDED 4 of 48 applicable (8.3%, Wilson [3.3%, 19.6%]) or 16 of 48 (33%, [22%, 48%]) depending on a convention (decision 1). |
| 5a Baselines head to head | done (demo, 5 seeds) | Baselines fire at 0% leakage. Leakage effect on downstream AUROC is indistinguishable from zero. |
| 5b full-scale same-pair | dropped (GPU, $8 cap) | Concede. |
| 5c Detector 1 prevalence baseline | done (existing artifacts) | Prevalence ratio is inverted: it flags legitimate cross-site comparisons more than real labeller mismatches (AUROC 0.059). |
| 5d / 5e | done | No baseline found for detector 4 in two queries; detector 5 out-of-scope paragraph written. |
| 6 Detector 5 restricted components | done | The false negative is instantiation-dependent (pre-stated reading). |
| Citations | partial | Two verified (Yang et al.; Subotić et al.). Anything else must be verified before use. |

## 3. Paper claims that change (unfavourable to current wording)

1. **Abstract and section 6.2, detector 1: "worse with data, not better".**
   The comparison mixed two estimands. 0.216 (demo) is a whole-cohort bootstrap;
   0.484 (full) is a 500-patient audit draw. Like for like the flag probability is
   about 0.22 at both scales (predicted 0.217 at full, never archived), and the
   demo CI [0.527, 0.774] contains the full-cohort kappa 0.602. What survives: at
   full scale the verdict is a coin flip (0.484, predicted 0.475). The demo
   cohort could not resolve it.
2. **"The eICU control is the discriminating counterexample."** By the
   pre-registered rule (discriminating iff margin <= 3 SD) it is a ceiling
   control at 5.4 SD. The only discriminating detector 1 control is the MIMIC
   single-point one at 0.06 SD. 7 of 15 control margins have no archived
   dispersion.
3. **Detector 2 "clean 0% control".** The shipped 0% arm is compared with itself,
   so it cannot flag; TN = 1 is by construction. An exploratory (not
   pre-registered) four-replicate null gives 0 of 4 flagged, 95% interval
   [0, 0.60]. See decision 2.
4. **"Leakage moves downstream performance in the expected direction."** Change
   in target AUROC versus 0%: -0.0003 [-0.007, 0.006], +0.009 [-0.011, 0.030],
   +0.010 [-0.012, 0.032] at 5/20/100%. All intervals include zero. The target
   probe has about 3 to 7 positive stays per seed (prevalence 1.3% to 3.1%).
5. **"An order of magnitude larger" (baseline section).** The 0% source-to-target
   gap is 0.090 [0.039, 0.142]; point estimates support roughly an order of
   magnitude, but the seed-level ratio intervals reach 0.37 at 100% leakage.
6. **Detector 5 false negative.** "0.27 against a 0.30 gate, just under" is the
   mean of a quantity that straddles the gate: the original instantiation flags
   the flagship in 3 of 5 seeds. Restricted to MAP and HH it flags 5 of 5. But the
   restricted ratio is unstable on the same-site control (mean 2.9, range 0.16 to
   12.8 at 900 stays), so the composition gate is decorative on PhysioNet too.
   Also, the committed `external5.json` is a one-seed run showing variant A silent
   everywhere; the five-seed rerun shows A flagging 4 of 5 at 80% and 95%.
7. **Detector 3.** The sampled corpus has no undisclosed contamination (0 of 23
   real selection sites, Wilson upper bound 0.14), so the sensitivity the prompt
   hoped to report as "0/k with a denominator" has no k. 126 notebooks and 8
   unparseable files are outside the scan.

Things that survive and can be said plainly: detector 1's Type 2 model predicts
the observed flag probabilities (0.475 against 0.484, 0.211 against 0.216);
the baselines carry no information on detector 2's scenario; detector 2's signal
is real beyond corpus size (A1 minus A2, t = 7.7 at 20%).

## 4. Deviations and caveats the response should not hide

- D1 to D3 (declared in the pre-registration): paths; leak size is a fraction of
  the target leak pool, not the source set; the corpus-size arm applies.
- "900 stays per site" is nominal. The loader's filters leave 602 to 651 source
  stays, 669 to 675 pool stays and about 225 probe stays per seed.
- Task 2's extra source stays come from a separate draw with used patients removed
  by id; the shipped draw leaves none. The A3 mask-transplant arm is under-filled
  (about 0.22 against the target's 0.30 on a small test) because a transplant can
  only remove observations, so A3 versus A4 is not a clean contrast.
- Task 2 / 5a run on CPU on a single pod environment; the V100 run differed from
  the archive by about 1%, the CPU run reproduces it to six digits.
- Task 3f needed three changes to the tool's Docker build (base image, npm
  `--unsafe-perm`, Node 14). The unmodified Dockerfile does not build.
- Task 4 repository selection: the frozen rule returned 6 new repositories, two
  off-topic (BasicTS, fairseq2) for the fairness slot; two topics returned none.
  Nothing was swapped by hand. AIF360 was pinned only at clone time (`34877916b7`).
- **Labelling checks are one-sided.** A blind relabel by the same model is not
  blind, so none was run and no agreement figure exists. Twelve sites are in
  `USER_SPOTCHECK.md` awaiting the user's labels. Five of the six Task 3 spot-check
  sites are NOT_SELECTION, so that check is weak on the contaminated class.
- The third-party code was built and run only inside Docker; nothing was imported
  on the host. No patient-level files are in the repository.

## 5. Decisions needed

**Decision 1: which Task 4 number leads.** I treated NaN that arises only when
training diverges as outside supported use. That gives 4 of 48, 8.3% [3.3%, 19.6%]
(1 of 27, 3.7%, among verdict or selection sites). If divergence counts, 12 more
sites flip: 16 of 48, 33% [22%, 48%]. The rubric did not settle this in advance and
I chose the narrower reading, which lowers the count; both are in the ledger. The
pre-stated reading (4e) is that either outcome is reported with its denominator.
Recommendation: lead with the pair, "8% to 33% depending on whether divergence-only
NaN counts", and name the three positives (tableshift label NaN to 0, fairseq2
null-as-pass length filter, robustdg `max` swallowing a NaN test loss).

**Decision 2: whether to harden the detector 2 null.** The four-replicate null has
a Clopper-Pearson upper bound of 0.60, which is too weak to defend "FPR 0".
Twenty replicates per seed would tighten it to roughly 0.17 if none flag. It is
CPU-only, about 10 to 25 minutes on the existing pods or locally, no GPU cost. It
would be labelled exploratory in any case because it was not pre-registered.
Recommendation: run it unless the strategy agent prefers to concede the weak
interval as is.

Smaller choices where I made a call and the strategy agent may override:
dropped Tier 2 (GPU, 5b) rather than ask for an estimate, because the $8 cap and
the lack of a GPU pod made it infeasible; did not claim any specificity for
detector 3 because it issues no clean verdict; stated the false negative as
instantiation-dependent exactly as the pre-stated reading required.

## 6. What is left before the freeze

User: twelve spot-check labels; push the unpushed commits (everything
pre-registered is already on the remote). Code agent: paper edits for the seven
claims above; response text; the 4open.science mirror update; Checkpoint B and C
notes. Any new citation in the response must first be added to
`CITATIONS_VERIFIED.md` after checking its page.
