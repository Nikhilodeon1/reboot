# Pre-registration addendum 3: full-scale tier (Task 2 Tier 2 and Task 5b)

Written 2026-10-09, committed before any full-scale arm is run. Extends
PREREG_R1.md and PREREG_R1_ADDENDUM_2.md. Basis for running it: the user
confirmed on 2026-10-09 that the pod is free of charge, that the data-use
agreement permits holding the data there provided it is deleted afterwards, and
asked for as much as possible to be run. The $8 cap therefore does not bind this
tier, but the written time estimate below is still given before launch.

## Design (Task 2 Tier 2 and Task 5b share the same trained models)

- Source MIMIC-IV, target eICU, the shipped external protocol of
  `detectors/external/run_external2.py`: small test-mode model, 3 epochs, batch 16,
  probe = 25% of the target, leak pool = the next block of target stays capped at
  the source size, seeds 42..46, leakage 0/5/20/100%.
- **Deviation D4 from PREREG_R1.md (hold-out size), declared before any run.**
  PREREG_R1.md reserves a 10% source hold-out. With 74,829 MIMIC stays that is
  about 7,483, but the 20% level needs about 12,000 extra source stays (20% of a
  pool capped at the reduced source size), so a 10% hold-out cannot supply it. The
  hold-out is therefore **20%** (14,966 stays), fixed once (permutation seed 0) and
  shared by all seeds; the other 80% (59,863 stays) is the source for every arm,
  A0 included. This was decided from the cohort sizes alone, before any arm.
- Arms exactly as in PREREG_R1.md section 2, with L = 5% and 20% of the leak pool:
  A0 no leak; A1 L target stays (the shipped detector); A2 L extra source stays
  from the hold-out; A3 hold-out stays wearing the observation mask of distinct
  target stays, applied to raw_ts before forward-fill and normalisation; A4
  hold-out stays randomly masked to the target's per-variable fill. A1 is also run
  at 100% for the baselines.
- Decision rules, the missingness share R, its definedness condition and the
  significance tests are those of PREREG_R1.md (critical t 2.132, df 4). The
  corpus-size rule (r2 at least 0.5 r1 means confounded) applies unchanged. The
  pre-stated prediction from PREREG_R1.md (mixed, leaning values-dominated,
  0.25 < R < 0.6) is not revised after the demo result; the demo result is
  reported beside it.

## Task 5b read-offs (same models, no extra training)

For the A0 and A1 models at each level: frozen encoder, mean-pooled embeddings,
regularised logistic head fitted on the source (75/25 split for the in-domain
AUROC), evaluated on the target probe. Three standard checks with their shipped
thresholds (k-fold instability, train/test gap, external floor), detector 2's
paired test, and the signal-to-nuisance ratio, all as in 5a.
- **Label.** Primary: the Sepsis-3 label produced by the loaders (field `sepsis`),
  per PREREG_R1.md. Secondary, exploratory: hospital mortality
  (`mortality_hospital`, identical definition in both databases).
- Intervals and undecidable counts reported as in 5a.

## Gates and readings, fixed now

- Time estimate before launch: roughly 135,000 optimisation steps per seed (about
  675,000 over five seeds) plus probe evaluations. At 60 to 100 steps per second
  per process, five processes sharing the A10, that is about 1 to 3 hours of wall
  time. The first run reports its measured steps per second; if the projection
  for all runs exceeds 8 hours the tier is stopped and reported as not completed.
- If any arm cannot be built (insufficient hold-out), the shortfall is reported
  and only the buildable level is run.
- Outcomes are reported as found, whichever way they fall: values-dominated,
  mixed, missingness-dominated or undetermined at full scale; baselines flag or do
  not flag at 0%.
- Data handling: raw MIMIC-IV and eICU files and every per-stay cache live only
  under the pod's scratch directory and are deleted when the runs are done; only
  aggregates are written to the repository.

## Clarification added before any run (2026-10-09)

The loader field `sepsis` is the SOFA-based label computed in `single-point` mode
for both databases (`mimic_sofa_sepsis_labels` / `eicu_sofa_sepsis_labels`),
which is the Sepsis-3 operationalisation meant above. Comments in the loaders
that call it ICD-based are stale. The label's operational definition is the same
in both databases; detector 1 is a separate question about whether two
legitimate definitions agree.

## Addendum 3b: revised before any full-scale run (2026-10-09, evening)

Supersedes the pod-based execution plan above. Reason: the data-use terms the
owner works under, as recorded in the handoff note for this machine, do not allow
credentialed MIMIC-IV or eICU-CRD files, or any patient-level derivative of them,
to be uploaded to a pod. The earlier statement that holding them on the pod was
acceptable is superseded by that stricter rule. The pod is not used for this tier,
and the fetch helper written for it is removed.

Changes to the design, all fixed before any run:

1. **Execution: this machine, CPU, no GPU.** The earlier time estimate (1 to 3 h
   on a GPU) no longer applies. Written estimate: about 84,000 optimisation steps
   per seed (arms A0, A1 at 5/20/100%, A2 at 5/20%), roughly 420,000 over five
   seeds. At an assumed 10 to 20 steps per second per process that is about 70 to
   140 minutes per seed and, with two or three processes, 3 to 6 hours of wall
   time. The first run reports its measured speed; if the projection for all runs
   exceeds 9 hours the tier is stopped and reported as not completed.
2. **Data: existing full-cohort preprocessed caches** (74,607 MIMIC-IV stays and
   130,446 eICU-CRD stays, built by the repository's own loaders; 17 variables, 48 h
   window, SOFA-based single-point Sepsis-3 label) instead of a fresh parse, which
   took 7 hours for MIMIC-IV alone. The cohorts differ slightly from the 74,829
   and 132,900 used elsewhere because the caches apply the loaders' extra filters.
   The caches hold fixed-bounds scaled values and the post-forward-fill mask, **not
   the raw pre-forward-fill series**.
3. **Arms A3 and A4 cannot be built** from these caches (they need the raw
   observation pattern before forward-fill) and are not run at full scale. So the
   missingness share R is undetermined at full scale, and the full-scale tier
   answers only: the corpus-size control (r2 against r1, the pre-registered 0.5
   rule) and the Task 5b baselines. No substitute manipulation on the post-fill
   mask is used, because it would not be the same intervention.
4. Everything else is as in addendum 3: 20% source hold-out for A2, A0 rerun on the
   80% source, probe 25%, pool capped at the source size, seeds 42..46, 3 epochs,
   same decision rules and readings.
5. Per-stay arrays derived from the caches are written only to a local scratch
   folder outside the repository, never committed and never moved off this machine.
   Only aggregates are written to the repository.
