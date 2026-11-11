# Suggested updates for the `confound-audit-paper-rules` skill (paste what you want; I did not edit the skill file)

The skill was written on 2026-10-09 and has been overtaken by results. Where it and the ledger disagree the ledger wins, as the skill itself says. Changes to make:

**Detector 3 line.** Replace "0 contaminated of 53 sampled sites (0 of 23 real selections), indeterminate on 53 of 53, sensitivity undefined" with: registered labels 0 of 23 contaminated;
after four blind raters and our adjudication 1 of 23 (exact 95% interval 0.001 to 0.219), up to 3 of 24 (0.027 to 0.324) if two unresolved sites count; the detector returned indeterminate on
53 of 53 files, so its sensitivity is 0 of 1 to 0 of 3, defined and uninformative. The registered labels are kept as the primary figure and the correction is disclosed.

**Type 1 external line.** Keep "4 of 48 narrow, 16 of 48 broad" and add: one of the four narrow positives (robustdg) is tagged divergence-only in our labels, so ordinary-use-only is 3 of 48; four blind
raters give narrow 3 of 61, 3 of 56, 4 of 53 and 21 of 64 and broad 16 of 61, 13 of 56, 17 of 53 and 33 of 64, median kappa 0.50, so the counts are rubric-dependent; after adjudication the counts equal the
registered ones. Add: executed fuzz of public checkers, 6 of 23 undefined-input cells passed or returned a value with no warning (0.102 to 0.484; 5 of 22 without one mis-mapped cell); one measured
effect on a benchmark loader (stand-in file and model): 3,994 of 6,272 institutions labelled negative, accuracy +13.1 points.

**Detector 1 line.** Add the audit-size result: flag probability of the MIMIC-IV control 0.492 at n = 100 to 0.411 at n = 5,000; model supported at held-out sizes (maximum deviation 0.026); the model puts the
audit size that would settle the verdict at 62,500 of 74,829 stays.

**Detector 5 line.** Replace "Say consistent with, n = 5 per cell" with: the five-seed prediction was tested on 20 fresh seeds and held at n = 1200 (13 of 20, interval 0.408 to 0.846, predicted 0.417) and failed at n = 4000
(8 of 20, 0.191 to 0.640, predicted 0.148); five seeds understated the spread by about a factor of two.

**Detector 2 line.** Add the dose sweep: the volume-matched statistic flags where the shipped statistic does, with the corpus-size share 0.31, 0.22 and 0.48 at 5, 10 and 20 percent; its flags at 1 and 2 percent are
not read as detection.

**Planned additions list.** Mark as done: executed fuzz of public checkers (E1), Type 2 on public thresholds (E2, the four-fifths rule, mechanism only), flag probability against audit size for detector 1 (E3),
volume-matched statistic across doses (E5), mutation test (E6, see the ledger for the result). Still open: protocol mutation test of the audit protocol itself, a human second rater, volume-matched detector 2 at full scale.

**Target figures.** Figure 1 stage model, Figure 2 flag probability against audit size and margin, Figure 3 corpus-size control, Figure 4 external counts by labeller (all made).

**Banned wording to add.** "none was contaminated" without the adjudication; "validated" for any rater agreement; "independent" for a model rater that shares training with the first labeller.
