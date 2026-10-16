# What is in this directory

Aggregate results only — confusion matrices, kappa values, confidence intervals,
t-statistics, flag rates, per-repository file counts. No per-stay or per-patient
data. `.gitignore` excludes `*.npz`, `*.pkl` and `*.pt` here for that reason.
Use the data setup and detector commands in the root README to rerun the
analyses with your own credentials.

`run_all.py` reads `check{1,2,5}.json` for its cached rows and re-runs checks 3
and 4 live. It needs nothing else in this directory and no clinical data.

## Scale — read this before quoting a number

Some files are demo-scale and some are full-scale. They are not
interchangeable. The revised manuscript reports the full-scale figures.

    file                     scale   notes
    check1.json              demo    PhysioNet; the paper's full-scale row is in README
    check2.json              demo    PhysioNet Site A -> Site B
    check3.json              n/a     static analysis, scale-free
    check4.json              n/a     static analysis, scale-free
    check5.json              demo    PhysioNet, 1200 stays/arm, seed 0
    bootstrap_kappa.json     DEMO    n=117, kappa 0.651, P(flag)=0.216
    external1.json           demo    MIMIC-IV demo + eICU demo
    external2.json           demo    MIMIC-IV demo (117 stays) -> eICU demo
    external5.json           demo    eICU demo with controlled HCO3 ablation
    baselines.json           demo    the three standard checks, for comparison
    check2_fill_audit.json   demo    missingness confound audit for detector 2
    check5_sampling.json     n/a     sampling-sensitivity study, n=4000
    external3_repos.json     n/a     detector 3 on the original 4-file corpus
    external4_lineage.json   n/a     detector 4 lineage traces, own + external code
    scan_repos.json          n/a     detector 3 corpus scan, 735 files / 18 repos

`bootstrap_kappa.json` is a demo-scale bootstrap: kappa 0.651, CI [0.528,
0.776], P(flag) = 0.216 at n=117. Consult the revised manuscript for full-scale
figures; full-scale run logs are not included in this repository.
