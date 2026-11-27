# Which results were fixed in advance and which were not

Working record for the rewrite (the reviewer asked for a confirmatory-against-exploratory table). "Fixed first" means that the
specification was committed before the run (`PREREG_MANIFEST.txt`). It does not mean blind: several inputs were chosen after the
code under test had been read, and the table says so. The ledger rows hold the numbers and the full wording of each caveat.

| Experiment | What it asks | Status | What must be said with it | Plan for the paper |
|---|---|---|---|---|
| E3 | How often does detector 1 flag at a given audit size? | Fixed first (first specification) | The primary control's whole-cohort kappa interval contains the cutoff. The model's spread is taken from n = 500, so n = 500 is not an out-of-sample test of it | Keep |
| E8 | How common are near-threshold kappas among reasonable Sepsis-3 variants? | Fixed first (addendum 4) | A family we defined; not a prevalence in the literature | Keep |
| E17 | Do the five detectors pass undefined inputs? | Fixed first (addendum 9), not blind | Inputs were listed after reading the detector code | Keep; headline |
| E17b | How much depends on conventions in the code? | Exploratory, after the results | 14 of 22 without the five convention-defined cells | Keep next to E17 |
| E18 | Point rule against interval and zone rules | Fixed first (addendum 10) | The interval error check against a bootstrap used 100 audits | Keep |
| E18b | Share of decisive answers that oppose the cohort verdict | Exploratory, after the results, at a reviewer's request | Includes the never-decides comparison | Keep |
| E22 | Can an explicit undecidable state remove the silent passes? | Fixed first (addendum 13), not blind | Guards were written with the E17 cells known, so this is not new evidence about other inputs | Keep, short |
| E19 | Loader comparison on the benchmark's data file | Superseded | Unseeded model; did not reproduce | Remove; ledger only |
| E19b | The same with ten model seeds | Fixed first (addendum 15), after the reproduction failure | Our reconstruction of the split and model. Reported accuracy gap has an interval above zero in only 6 of 10 seeds. One of E19's two bounds is not met | Use only if E21 fails |
| E21 | The same with the benchmark's own code | Fixed first (addenda 12, 14, 15); not yet run | Only the download step is replaced | Primary loader result if it runs |
| E23 | Do 34 checks in 8 other libraries pass undefined inputs? | Fixed first (addenda 16, 17); not yet run | One labeler who knows the hypothesis. Harness written by a language model from documentation. Libraries not sampled | Add to main text whatever it shows |
| E13, E13b | Loader comparison on another official file with random splits | E13 fixed first (addendum 5, itself prompted by a mock review); E13b exploratory | Different file and split from the benchmark's | At most one sentence next to the loader result |
| E12, E12b | Consequences of the public-code cases | E12 fixed first (addendum 1); E12b exploratory | The cases came from reading repositories, not from a sample | Keep the cases; say how they were found |
| E1, E1b | Degenerate inputs to five packages | E1 fixed first (addendum 1); the unit and documentation checks followed | One a priori mapping was wrong (scikit-learn kappa); without it 5 of 22 | Rewrite decides; E23 is the stronger test |
| E6, E6b, E14 | Do the tests guard the detectors' decision lines? | E6 and E14 fixed first (addenda 3 and 5); E6b exploratory | Survivor roles assigned by the authors | Rewrite decides |
| E2, E2b, E2 reference | Four-fifths ratio on public data | E2 fixed first (addendum 1); the stratified and reference readings exploratory | | Cut |
| E4 | Detector 5 on fresh seeds | Fixed first (first specification); the refit exploratory | | Cut |
| E5, E5-full, E9, E16 | Detector 2 dose, missingness and extra seeds | Fixed first (addenda 3, 4, 7, 8) | Seeds from two processors | Cut except the sentence that corpus size confounds detector 2 |
| E7, E15 | Language-model raters and an outside coder | Specified in addenda 2, 2b and 6; exploratory readings follow | The coder's provenance is not confirmed | Cut (decided 2026-11-26) |

Two runs failed or changed after the specification: E19 (above) and the E21 runtime (addendum 14, changed before any run). The E23
dependency rule (addendum 17) was also set before any run.
