# Open items for the TMLR paper (v2/paper/main.tex)

Working notes. Not part of the manuscript or the supplementary archive. What is wrong with the current paper is in
`PAPER_REVIEW.md`; which results were fixed in advance is in `EXPERIMENT_STATUS.md`.

## Where things stand (2026-11-27)

1. **Methodology:** waiting on E21 and E23. Both run from `pclCodebase/colab_upload/methodology_runs.ipynb`. E23 needs the
   author's 53 labels first, given with no assistant. E21 gate: if the benchmark pipeline removes rows without a
   completion rate, delete the loader claim.
2. **Then:** analyse (`v2/scripts/e23_analyse.py`), add ledger rows, rebuild the supplement
   (`pclCodebase/tools_private/build_supplement.py`).
3. **Then:** rewrite. Approved cuts: repository reading, outside coder, raters. Also cut detector 2 and detector 5 detail and
   the four-fifths illustration. Fix every P0 item in `PAPER_REVIEW.md`. The manuscript still shows the E19 numbers.
4. **Then:** the authors' own pass (below) and final checks.

Do not push while the repository is public. Home-folder paths are in files that earlier commits contain.

## Only the authors can do these

- AI-use statement and TMLR's note on language-model use (`main.tex`, comment near the end of the main text).
- Rewrite the passages in `AUTHOR_PASS.md` in their own words (refresh that file after the rewrite).
- Read the final PDF end to end; rerun and be able to explain the headline results, the 0.60 cutoff, the 500-stay audit
  and the three-standard-deviation margin.
- Check the citations that were verified at metadata level only.
- TableShift follow-up note: on hold until E21 (`DISCLOSURE_DRAFTS.md`, local only). Add a sentence if a maintainer replies.
- Decide whether and when to submit.

## Known limits that stay unless someone does the work

- No patient-level bootstrap: patient identifiers of the full cohorts are not on the analysis machine.
- No replacement control for detector 1 and no equivalence-test design.
- One labeler for E23.
- The reporting standard has not been applied by an independent person. A rating file of unestablished authorship is kept
  outside the repository and is not used.
- E17 was not blind: its inputs were listed after reading the detector code.
- The paper pools 19 of 27 cells with an interval although addendum 9 said cells would not be pooled.
- The mock reviewer's suggested citations (Ethayarajh 2020; Cherian and Candes; Snoek et al. 2019) are not verified and not
  added. Schuirmann 1987 is verified at abstract level and not yet cited.

## Checks that exist

- `python v2/scripts/reproduce.py` (options in its docstring) compares reruns with committed results.
- `python -m pytest detectors/tests`: 108 pass, 7 skip without PhysioNet data.
- `python v2/scripts/cite_check.py`.
- `pclCodebase/lintkit/paperlint.py` (hash-verified copy of the writing skill's linter).
