# Open items for the TMLR paper (v2/paper/main.tex)

Working notes. Not part of the manuscript or the supplementary archive.

## Needs you (a person or an account that I do not have)

1. **AI-use statement and the TMLR note on LLM use.** Write from what was done. The source file has a comment where it goes.
2. **Benchmark's own data file (E19).** The College Scorecard task of the benchmark reads `Scorecard.csv` from the Kaggle dataset `kaggle/college-scorecard`, which needs a Kaggle login. Download it, then run `python -W ignore v2/scripts/e19_tableshift_own_file.py --data <folder with Scorecard.csv>`. The script reproduces the benchmark's domain split, default model and verbatim preprocessing (read from its source at commit fca9429814, not imported) and has only been smoke-tested on synthetic data. Send me `v2/results/e19_tableshift_own_file.json` and I will add it to the paper and the ledger. Until then the paper states the limit.
3. **Independent application of the reporting standard.** The kit is in `v2/validation_kit/`. Steps: fill and commit `answers_authors.csv` (about 1 hour), send the rater `CARD.md`, `CASES.md` and `answers_template.csv`, run `score_agreement.py`. The paper says the standard is unvalidated and stays that way until this is done.
4. **Patient-level bootstraps.** The patient identifiers of the full MIMIC-IV and eICU-CRD cohorts are not on this machine. If you run on the machine that has the credentialed tables, a cluster bootstrap over patients for the whole-cohort kappa and the audit draws would replace the stay-level intervals. The paper states the limit.
5. **Maintainer replies.** Two of three maintainers were notified on 2026-11-23. Add a sentence if one replies.
6. **Rewrite the passages in `v2/AUTHOR_PASS.md`** in your own voice, keeping the numbers.
7. **Read the final PDF end to end**, and decide whether to submit.

## Done in this pass

- Retitled to "Can This Check Fail? An Audit of Five Clinical Confound Detectors". The failure modes are now silent pass (undefined-input pass and weak-control pass) and threshold sitting. The two development hazards moved to the limitations.
- E17 (addendum 9): executed degenerate-input test of the five detectors, 19 of 27 undefined cells return a clean verdict. This is now the headline evidence and replaces the rubric-counted prevalence.
- E18 (addendum 10): the point rule against an interval rule and a bootstrap zone rule on 90 pair and database combinations, the interval rule never resolving the primary control, and prevalence-adjusted kappa.
- E16 (addenda 7 and 8): detector 2 near-threshold readings with 20 seeds; two verdicts changed.
- Detector 2, detector 3 outside its home idiom, and the repository reading moved to appendices. The main text ends on page 11.
- Detector table added to Section 4. Tables for E17 and E18 added to the main text and the appendix. Figure 4 label fixed.
- The loader paragraph now says our model is the benchmark's default `histgbm` configuration (library defaults). The remaining differences are the data file, the domain split and the feature discretization.
- Code supplement rebuilt with the new scripts and results (108 tests pass, 7 skip).
- One fresh-eyes mock review run on the compiled text (see the report that came with this commit).

## Deviations to know about

- Addendum 9 said cells would not be pooled across detectors, but the paper reports 19 of 27 with a descriptive interval. The paper says the interval treats the cells as independent although they are not.
- The E17 input list was written after reading the detector code, so the outcomes are not blind. The paper says so.
- Addendum 10's zone rule uses 200 audits for six pairs, and the interval rule's standard error is an approximation checked against a bootstrap on 100 audits.

## Reviewer points not addressed

- Citations the reviewer suggested and I could not verify: Schuirmann 1987 (equivalence testing), Ethayarajh 2020, Cherian and Candes, Snoek et al. 2019. Not added.
- Independent coding of all 88 sites by two humans, and pinned model snapshots for the language-model raters. The paper no longer reports a prevalence, and states both limits.
- Equivalence-test or dose-response controls for detector 1 (a new design, not run).

## Tooling

- `paperlint.py` v3 is extracted from the skill and verified (hash 2b87a01d49cc2ae3...). The skill file on disk had doubled backslashes inside the code block, so I reversed that escaping before the hash matched. Remaining lint items: 30 "number not in ledger" (rounding, table widths, hash prefixes, repository line numbers, "AI Fairness 360"), file names in appendix site locations, number walls in appendix text, and benign word matches.
- The AAAI-format paper in `cane_ai/` is stale (five-seed numbers, old title) and should not be used.
