# Pre-registration, v2 (TMLR resubmission), section 1

Committed before any run in this document. Later sections are added as addenda, each committed before the
experiment it covers runs. Predictions below are computed from round-1 archived values only (commit hashes in
`v2/evidence_r1/rebuttal/LEDGER.md`). A deviation is declared in an addendum before the affected run, not after.

General rules: no detector or threshold is edited; shipped functions are called unchanged; per-stay arrays and
labels stay outside the repository and only aggregates are written under `v2/results/`; intervals for
proportions are exact Clopper-Pearson (95%); seed lists and draw counts are fixed here.

## E3. Detector 1: flag probability against audit size

**Question.** Does the Type 2 model, fitted at one audit size, predict the flag rate at other audit sizes?

**Data.** Full-scale detector 1 labels (MIMIC-IV, N = 74,829; eICU-CRD, N = 132,900), regenerated in round 1 by the
unchanged runner and held outside the repository. Cases:
(a) MIMIC control: SOFA win[-48,+24] against SOFA single-point; (b) eICU positive: ICD against SOFA win[-48,+24];
(c) eICU control: SOFA win[-48,+24] against SOFA single-point.

**Procedure.** Flag rule of the shipped detector: kappa < 0.60 on the audit subset. For each case and each audit size
n in {100, 200, 500, 1000, 2000, 5000}, draw R = 2000 audit subsets of n stays without replacement (numpy
`default_rng`, seed 90000 + 100 * case_index + size_index), compute kappa as the shipped `cohens_kappa`, and flag if kappa < 0.60.
Draws with undefined kappa are counted as undecidable, reported separately, and excluded from the flag rate.
Observed flag rate p_obs(n) with exact 95% interval over the decidable draws.

**Prediction, fixed now.** theta* = whole-cohort kappa and sigma_500 = the audit-draw SD at n = 500, both read from
the round-1 file `full_scale_bootstrap_kappa.json` (MIMIC control 0.6019 and 0.0320; eICU positive 0.4510 and 0.0576;
eICU control 0.8260 and 0.0419). Then
sigma_n = sigma_500 * sqrt((500 / n) * (N - n) / (N - 500)) and p_hat(n) = Phi((0.60 - theta*) / sigma_n).
No parameter is refitted after seeing p_obs.

**Reading rule, fixed now.** For each case let D = max over n in {200, 500, 1000, 2000} of |p_hat(n) - p_obs(n)|.
Supported if D <= 0.05; partly supported if 0.05 < D <= 0.10; not supported if D > 0.10. The sizes 100 and 5000 are
reported but outside D (kappa is skewed at 100; the finite-population correction is large at 5000 for the eICU
cohort's smaller prevalence). The reading for the whole model is the weakest reading across the three cases.

**Derived quantity.** The audit size n* at which p_hat(n) <= 0.05 or >= 0.95 for case (a), solved from the model.
If n* exceeds N, the paper states that no audit of this cohort resolves the verdict.

**Where.** Local CPU. Script `v2/scripts/e3_d1_audit_size.py`.

## E4. Detector 5: fresh-seed test of the Type 2 prediction

**Question.** Do fresh seeds flag at the rates the first five seeds predicted?

**Procedure.** The shipped `run(seed, n)` of `detectors/checks/check5_missingness_scale.py`, unchanged, on PhysioNet
2019 (open data), positive case Site A against Site B and negative case Site A against itself, variant A
conjunction (composition gap ratio > 0.30 and max availability ratio > 2.0). Seeds 5 to 24 (20 new seeds, none used
in round 1) at n = 1200 and at n = 4000 stays per arm. Record the per-seed ratio, availability ratio and flag for
both cases.

**Prediction, fixed now.** From the round-1 five-seed statistics (ledger row A2-d5-1200, A2-d5-4000):
P(flag) = 0.417 at n = 1200 (mean 0.283, SD 0.082) and 0.148 at n = 4000 (mean 0.272, SD 0.027), where
P = Phi((mean - 0.30) / SD).

**Reading rule, fixed now.** Consistent if the predicted probability lies inside the exact 95% interval of the observed
flag count out of 20; otherwise not consistent. Also reported, not used for the reading: mean and SD of the fresh
ratios against the round-1 mean and SD, and the flag count of the negative control (expected 0 of 20).

**Where.** Local CPU or a pod; PhysioNet 2019 only. Script `v2/scripts/e4_d5_fresh_seeds.py`; seeds run in
parallel processes, one file per seed and size.

## Not yet registered (addenda before they run)

E1 (executed fuzz of public checkers), E2 (Type 2 on public thresholds), E5 (detector 2 v2), E6 to E10, and the
E7 rating protocol. Each gets its own addendum with its frozen lists and reading rules.
