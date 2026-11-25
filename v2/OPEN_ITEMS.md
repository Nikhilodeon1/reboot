# Open items for the TMLR paper (v2/paper/main.tex)

Working notes. Not part of the manuscript or the supplementary archive.

## Authors to do

- Write the AI-use statement and the TMLR first-page note on LLM use. The statement should cover writing, code, labeling and citation checking, and should say what the authors checked by hand. The source file carries a comment where it goes.
- Read the compiled PDF end to end. Rewrite the passages in `author_pass.md` in your own words, keeping every number, interval and citation.
- Refresh the anonymized code supplement with the E16 script (`v2/scripts/e9_full_scale.py`, `e16_lane.sh`), the E16 and E13b results, and addenda 7 and 8.
- Answer one question the reviewer asked and the paper does not: which setting forces a subset audit for detector 1? If none does, say so in Section 5.3.

## Done in this pass

- Maintainer notification: two of three repositories notified on 2026-11-23, the third (archived, read-only) could not be. Stated in the Broader impact paragraph.
- Abstract cut from about 290 to about 190 words, with fewer numbers.
- Page limit: the conclusion now ends on page 12. Detector 5 and the four-fifths simulation moved to the appendix with a two-sentence summary in Section 5.3. The four-fifths simulation is no longer listed as an external instance of Type 2.
- Detector 3's abstentions are no longer listed as a Type 1 instance in Table 1.
- Added the 1.64 against 3 margin explanation, a note on what a user does with an inconclusive verdict, a no-multiplicity-adjustment statement, and a kappa and prevalence caveat.
- Positive controls no longer carry a ceiling or discriminating class. The reporting card note is no longer numbered as item 6.
- Three related-work citations verified and added: negative controls (Lipsitch et al. 2010), sanity checks (Adebayo et al. 2018), kappa and prevalence (Feinstein and Cicchetti 1990). The Feinstein and Lipsitch entries rest on the abstract only.
- Fixed two broken cross-references that earlier scripted edits had introduced.

## Reviewer points not addressed (need a decision or new work)

- Title and scope: the title says clinical, the external evidence is general-purpose ML code.
- Rename Type 1 and Type 2 (they collide with statistical Type I and II errors), and the coined labels falsy-as-clean, ceiling control, structural non-discriminability.
- Define Type 1 by an executable test and count patterns, not occurrences. Treat loader coercion as its own category.
- Replace rubric-based prevalence with execution-based counts, or have two humans double-code all 88 sites with adjudication. Pin the model versions of the language-model raters.
- Reframe Type 2 as a short general result and evaluate the three-way verdict against a confidence-interval rule by simulation. Add a dose-response or equivalence-test control for detector 1.
- Validate the reporting standard on at least three external diagnostics with an independent rater, and map it to TRIPOD+AI, PROBAST and the ML Test Score.
- Run the TableShift loader task with the repository's own pipeline. Reconcile the two true-label AUROC deltas (-1.5 on overlapping splits, -0.5 in cross-validation).
- Move detector 2, the mutation test and the development hazards to appendices and cut the main text to about 10 pages.
- Resample patients, not stays, in the cohort bootstraps; report prevalence and a prevalence-adjusted kappa; use stays, patients and persons consistently.
- Clarify what detector 1 compares (two operationalizations in one cohort, per Section 4) against the wording in the detector appendix.
- Use "pre-specified" in Figure 4 and in the figure script (still reads "pre-registered"), and "open-data scale" in place of "demonstration scale" in the figure.
- Citations suggested by the reviewer and not added because they are unverified: Schuirmann 1987 (equivalence testing), Ethayarajh 2020, Cherian and Candes, Snoek et al. 2019.

## Tooling

- `paperlint.py` is still missing from the ml-paper-writer skill folder. This pass used a saved copy of an earlier version, so macro, venue-overlap and TeX-log checks did not run. Remaining lint errors are 26 "number not in ledger" items, which are rounding, table widths, repository line numbers and "AI Fairness 360".
- The AAAI-format paper in `cane_ai/` still carries the five-seed detector 2 numbers and a pending-rerun placeholder. Update it from the E16 rows before any further use.
