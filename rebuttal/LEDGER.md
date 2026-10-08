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
