# Rebuttal ledger

Every number the writing agent may use. One row per value. Nothing is quotable
in the response unless it appears here with a source file and a command.

Conventions: `scale` is demo or full plus n stays per site; `n` is the
denominator the value is computed over; `seeds` is the seed count (`-` for
deterministic); `MISSING` where an artifact was never archived.

| id | value | meaning | scale | n | seeds | source file | command | commit |
|---|---|---|---|---|---|---|---|---|
| T1a-prec-pooled | 1.000 [0.541, 1.000] | pooled precision, Clopper-Pearson 95% | mixed (heterogeneous; reference only) | 6 | - | rebuttal/tables/task1a_exact_intervals.csv | python rebuttal/scripts/task1_stats.py | c347561 |
| T1a-rec-pooled | 0.857 [0.421, 0.996] | pooled recall | mixed (reference only) | 7 | - | rebuttal/tables/task1a_exact_intervals.csv | python rebuttal/scripts/task1_stats.py | c347561 |
| T1a-fpr-pooled | 0.000 [0.000, 0.265] | pooled FPR | mixed (reference only) | 12 | - | rebuttal/tables/task1a_exact_intervals.csv | python rebuttal/scripts/task1_stats.py | c347561 |
| T1b-d1-mimic-full | m = 0.06 (discriminating) | MIMIC win vs single-point margin to tau=0.60 in SD units | full, n=74829 | 500-draw audit | 5000 resamples | rebuttal/tables/task1b_control_margins.csv | python rebuttal/scripts/task1_stats.py | c347561 |
| T1b-d1-eicu-full | m = 5.40 (ceiling) | eICU win vs single-point margin; paper calls this the discriminating counterexample | full, n=132900 | 500-draw audit | 5000 resamples | rebuttal/tables/task1b_control_margins.csv | python rebuttal/scripts/task1_stats.py | c347561 |
| T1b-missing | 7 of 15 | control margins with no archived dispersion (z MISSING) | mixed | 15 | - | rebuttal/tables/task1b_control_margins.csv | python rebuttal/scripts/task1_stats.py | c347561 |
| T1c-mimic-full | predicted 0.475 vs observed 0.484 | Type 2 flag-probability model, audit-draw estimand | full, n=74829 | 500-draw audit | 5000 resamples | rebuttal/tables/task1c_flag_probability_model.csv | python rebuttal/scripts/task1_stats.py | c347561 |
| T1c-mimic-demo | predicted 0.211 vs observed 0.216 | same model, cohort-bootstrap estimand | demo, n=117 | 117 | 2000 resamples | rebuttal/tables/task1c_flag_probability_model.csv | python rebuttal/scripts/task1_stats.py | c347561 |
| T1c-estimand | 0.216 (cohort) vs 0.484 (audit draw) | the paper's demo->full comparison mixes estimands; like-for-like cohort value at full scale is 0.217 predicted | demo and full | - | - | rebuttal/results/task1_estimand_audit.json | python rebuttal/scripts/task1_stats.py | c347561 |
| T1c-band | MIMIC 0.602 vs eICU 0.826 | same implementation pair, different databases: legitimate-variation band for Type 2 | full | 2 databases | - | rebuttal/tables/task1c_legitimate_variation_band.csv | python rebuttal/scripts/task1_stats.py | c347561 |
| T3a-sites | 103 | candidate selection sites over 18 pinned repos, frozen patterns P1-P4 (61/10/12/20) | corpus | 18 repos, 688 .py files parsed | - | rebuttal/results/task3a_counts.json | python rebuttal/scripts/task3a_enumerate.py | script b845cc0 |
| T3a-sampled | 53 | sites sampled, at most 5 per repo, seed 20261006; cap of 60 not reached | corpus | 103 | - | rebuttal/results/task3a_sample.json | python rebuttal/scripts/task3a_enumerate.py | script b845cc0 |
| T3a-coverage-gap | 126 notebooks, 8 unparseable files, 3 repos with 0 sites | notebooks not scanned; Python 2 or broken files counted as unparseable, never clean | corpus | 18 repos | - | rebuttal/tables/task3a_counts_by_repo.csv | python rebuttal/scripts/task3a_enumerate.py | script b845cc0 |
| T3b-labels | 0 CONTAMINATED, 1 DISCLOSED_ORACLE, 1 AMBIGUOUS, 21 SOUND, 30 NOT_SELECTION | outcome labels for the 53 sampled sites; labels committed at e82be15 before detector 3 ran | corpus | 53 sites | - | rebuttal/results/task3b_labels.json | hand labelling by RUBRIC_3B.md | e82be15 |
| T3b-prevalence | 0/23 contaminated, Wilson 95% [0.000, 0.143]; 1/23 disclosed oracle, [0.008, 0.210] | among the 23 sites that are real selections (SOUND + oracle + ambiguous); sites are not independent (15 distinct files) | corpus | 23 | - | rebuttal/results/task3b_labels.json | python Wilson on the label counts | e82be15 |
| T3c-verdicts | 53 of 53 INDETERMINATE under both vocabularies | detector 3 verdicts on the file of every labelled site, 36 distinct files; file-level verdict joined to site-level label | corpus | 53 | - | rebuttal/results/task3c_verdicts.json | python -W ignore rebuttal/scripts/task3c_run_detector3.py | e82e190 |
| T2-r1-20 | 0.0901 | mean relative probe-loss reduction, A1 (shipped detector) vs A0, 20% leak | demo, PhysioNet A to B, source 602-651 stays, pool 669-675, probe 222-225 | per seed | 5 | rebuttal/results/task2_demo.json | PCL_TEST_MODE=1 python rebuttal/scripts/task2_values_vs_missingness.py --seed N (N=42..46), then --analyse | pending |
| T2-r2-20 | 0.0436 | same, A2 (extra source stays, corpus-size control); r2/r1 = 0.483 | demo | per seed | 5 | rebuttal/results/task2_demo.json | as above | pending |
| T2-r3-r4-20 | 0.0385, 0.0584 | A3 joint-mask transplant, A4 marginal-fill match, 20% | demo | per seed | 5 | rebuttal/results/task2_demo.json | as above | pending |
| T2-R | 0.02 at 5%, -0.11 at 20% | missingness share R = (r3-r2)/(r1-r2), defined because A1-A2 t = 8.18 and 7.67 clear 2.132; verdict values-dominated at both | demo | per seed | 5 | rebuttal/results/task2_demo.json | as above | pending |
| T2-actual-n | source 602-651, not 900 | the nominal 900 stays/site is reduced by the loader's filters; the shipped detector's demo has the same property | demo | 5 seeds | 5 | rebuttal/results/task2_seed42.json .. 46 | as above | pending |
| T4a-selection | 6 new repositories chosen by the frozen rule; topics 4 and 5 yielded none | star-sorted GitHub search, Python, README paper link, not already included; rule frozen in bc365cf before any query | corpus | 5 queries | - | rebuttal/results/task4a_selection.json | python rebuttal/scripts/task4a_select_repos.py | bc365cf |
| T4b-sites | 236 sites, 88 sampled | S1-S4 candidate sites over 25 repositories (18 pinned, AIF360, 6 new); patterns frozen in 073d042 | corpus | 25 repos | - | rebuttal/results/task4b_counts.json | python -W ignore rebuttal/scripts/task4b_enumerate.py | 073d042 |
| T4c-labels | 4 REACHABLE_UNGUARDED, 20 GUARDED, 24 UNREACHABLE, 40 NOT_APPLICABLE | labels for the 88 sampled sites by RUBRIC_4C.md, committed 879d885 before reading any site | corpus | 88 | - | rebuttal/results/task4c_labels.json | hand labelling | pending |
| T4c-proportion | 4/48 = 8.3%, Wilson 95% [3.3%, 19.6%] | REACHABLE_UNGUARDED among applicable sites, divergence-NaN treated as outside supported use; positives sit in 3 files | corpus | 48 | - | rebuttal/results/task4c_labels.json | Wilson on label counts | pending |
| T4c-verdict-kind | 1/27 = 3.7%, Wilson [0.7%, 18.3%] | same, restricted to verdict or selection sites | corpus | 27 | - | rebuttal/results/task4c_labels.json | Wilson on label counts | pending |
| T4c-alt-convention | 16/48 = 33.3%, Wilson [21.7%, 47.5%] | same, if divergence-type NaN counts as supported use; 12 sites flip | corpus | 48 | - | rebuttal/results/task4c_labels.json | Wilson on label counts | pending |
