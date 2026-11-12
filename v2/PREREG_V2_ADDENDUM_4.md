# Pre-registration, v2, addendum 4: E8 (a family of Sepsis-3 operationalizations), E9 (full-scale missingness arms), E5-full (dose sweep at full scale)

Committed before any of the runs below. Convention as in the earlier documents: specification by commit order. Nothing here changes a detector, a
threshold or a shipped function. Credentialed data and anything derived from them per stay stay outside the repository; only aggregates are written
under `v2/results/`.

Motivation: a mock review of the paper pointed out that Type 2 rests on one coincidence among six full-scale pairs (kappa 0.602 against 0.60),
that the missingness arms of detector 2 exist only at demonstration scale, and that the volume-matched dose sweep is demonstration scale only.

## E8. How often do defensible Sepsis-3 operationalizations land near the kappa threshold?

**Question.** Among operationalizations of Sepsis-3 that differ only in how the SOFA change is timed against the suspected infection, in what share
of pairs does the whole-cohort kappa lie close enough to 0.60 that the 500-patient audit flag probability is between 0.05 and 0.95?

**Family, fixed now.** Suspected infection, the SOFA components, the 24-hour worst-value look-back and the threshold SOFA >= 2 are exactly as shipped
(`src/data/sofa_sepsis.py`, `_mimic_suspicion`, `_sepsis_from_series`). The only axis varied is the SOFA window around the suspicion time, in hours
before and after: (pre, post) in {24, 48, 72} x {12, 24, 48}, plus the single-point rule (0, 0). That is 10 operationalizations and 45 unordered pairs per
database. The pair (48, 24) against (0, 0) is the pair of the paper's Type 2 case; (48, 24) against (24, 12) and against (72, 24) are two of its
negative controls. Other axes (the suspicion rule, the look-back, the threshold) are not varied and the paper will say so.

**Computation.** Components are read once with the shipped `mimic_sofa_components` and `eicu_sofa_components` and cached in shards outside the repository.
Each variant is scored by calling the shipped `_sepsis_from_series` per stay. Validation before anything is reported: the four variants of the earlier
runs, (48,24), (0,0), (24,12) and (72,24), must reproduce the stored full-scale labels exactly for every stay in both databases. If any stay differs, the
run stops and the discrepancy is reported.

**Statistics, per database and pair.** Whole-cohort kappa (the shipped `cohens_kappa`), the standard deviation of the kappa of 500-patient audit draws
(2,000 draws, seed fixed in the script), the margin m = |0.60 - kappa| / sd, and the flag probability (share of draws with kappa below 0.60, the shipped
rule). Pairs whose audit kappa is undefined in more than 1% of draws are reported as undecidable and left out of the counts, with their number.

**Pre-stated prediction.** Fewer than 10% of the 45 pairs per database have a flag probability between 0.05 and 0.95. Reading rule: if the exact 95%
interval for the share of pairs in that zone lies wholly above 0.10 we say the position near the threshold is common in the family; if it lies wholly
below 0.10 we say it is rare; otherwise we say the family does not settle it. Pairs share variants, so the 45 are not independent, and the family is of our
choosing; the paper will say both.

**Where.** Local CPU for the cache; the analysis can also run from the cache alone on any machine. Scripts `v2/scripts/e8_build_sofa_cache.py`,
`v2/scripts/e8_family.py`.

## E9. Missingness arms A3 and A4 at full scale

**Question.** At full scale (MIMIC-IV to eICU-CRD), is detector 2's effect carried by target values or by the target's observation pattern?

**Design.** The arms are those of the earlier demonstration-scale run (`task2_values_vs_missingness.py`): A3 adds the extra source stays (the same extra
stays as A2, same permutation seed) wearing the observation mask of a distinct random target stay, applied to the raw series before forward-fill and
normalization; A4 randomly masks the extra source stays to the target's per-variable fill. Levels 5% and 20% of the pool, seeds 42 to 46, the small model,
3 epochs, CPU, and the same split, pool and probe indices as the full-scale tier (`tier2local_seed*.json`). A0, A1 and A2 are taken from those seed
files; the run refuses to proceed unless the environment fields (torch, numpy, epochs, device, split sizes) in those files match. The raw series before
forward-fill are re-extracted by running the shipped loaders `load_mimic4` and `load_eicu` unchanged (full data, seed 0, `keep_raw=True`), with only the
sepsis-label call replaced by a stub in the calling script, because the labels are not used. Validation: preprocessing the raw series with the shipped
`preprocess_timeseries` must reproduce the stored `values` arrays for every stay; otherwise the run stops.

**Reported and read.** Per level: r1, r2, r3, r4 (mean relative reductions in probe loss against A0), t-statistics as in the demonstration run, and the
quantity R = (r3 - r2) / (r1 - r2) when A1 against A2 clears t >= 2.132. The reading rule is the earlier one: R <= 0.25 with t(A3 - A2) below the
critical value reads as values-dominated; R >= 0.75 with t(A1 - A3) below it reads as missingness-dominated; otherwise mixed; undetermined when A1 does
not clear A2. **Pre-stated prediction:** values-dominated or mixed, not missingness-dominated (the demonstration result was values-dominated).

## E5-full. Dose sweep with the volume-matched statistic at full scale

**Design.** As addendum 3 (E5), at full scale: doses 1%, 2% and 10% are new; 5% and 20% come from the full-scale seed files. Arms A1 and A2 only, seeds
42 to 46, same protocol and split as E9. v1 is the shipped statistic (A1 against A0, one-sided t on the five seeds, critical value 2.132) and v2 is the
paired difference A1 minus A2 from the same models. Pool sizes: 1% = 597, 2% = 1,194, 10% = 5,969 stays of the 59,686-stay pool, all within the
14,921-stay hold-out that supplies the extra source stays.

**Reported.** Per dose r1, r2, r2/r1, t for v1 and v2 and whether each flags; the lowest dose at which each flags. The reading rule is that of addendum 3
with one addition fixed now: where v2 flags and v1 does not, and r2 is within 0.005 of zero, the flag is not read as detection, because v2 is then the
difference of the leaked arm against a corpus-size arm that has not moved. No null is rerun for v2 at these doses and the paper will say so.

## Compute, resumability and data handling

Every run is split into tasks that write one small result file each, atomically, and skip tasks whose file exists, so an interrupted run resumes without
loss. Labelling and extraction are staged the same way. The component cache for E8 and the pre-forward-fill arrays for E9 are patient-level derivatives of
credentialed data. They are written outside the repository and stay on the owner's machine and private storage. Nothing from them is committed.
