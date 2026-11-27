# Open items for the TMLR paper (v2/paper/main.tex)

Working notes. Not part of the manuscript or the supplementary archive.

## Roadmap in progress (review of 2026-11-26; approved: cut repository reading and raters, patch detector copies, run third-party code in the authors' Colab, skip the replacement control, one human labeler)

- Done: Phase 0 consistency fixes; 1a baselines (E18b); 1d patched copies (E22).
- Waiting on the author: E21 and E23 in Colab, one notebook in pclCodebase/colab_upload/ (addenda 12, 14, 15 for E21; addendum 16 for E23). E23 needs the author's 53 labels first, given with no assistant. E21 gate: if the benchmark pipeline removes rows without a completion rate, delete the loader claim.
- Then: analyse E21 and E23 (`v2/scripts/e23_analyse.py`), ledger rows, rebuild the supplement. That ends the methodology work. Then Phase 2 cuts and rewrite, Phase 3 author ownership, Phase 4 final checks.
- Reproduction check (2026-11-26), from a clean copy of the committed repository: E3, E8 analysis, E6 (mutation test), E13, E13b, E17, E18 and E22 returned identical result files; the 108 detector tests passed (7 skipped). E19 did not (unseeded model): replaced by E19b. The paper still shows the E19 numbers: replace them with E21, or E19b, in the rewrite. In E19b the reported accuracy gap has an interval above zero in only 6 of 10 seeds, so the paper must not say that reported accuracy is higher. The E16 and E18b analysis scripts and the seed 42 to 46 losses were not in the repository; they are now, and reproduce the committed summaries exactly. Not rerun: E1 (needs the third-party container), E9 and E16 training (hours of compute; their stored losses were reanalysed).
- Paper updates owed by these changes: appendix list of specification documents (now 16 plus 2B and the first), the loader paragraph and abstract.
- The GitHub repository should be private and nothing should be pushed until that is decided.

## Needs you (a person or an account that I do not have)

1. **AI-use statement and the TMLR note on LLM use.** Write from what was done. The source file has a comment where it goes.
2. **E19 is done** (benchmark's own `Scorecard.csv`, 2026-11-26). The reported AUROC gain of the official-file comparison does not carry over (-0.8 points); the benchmark's reported accuracy is 2.0 points higher unguarded, and on observed-label rows the unguarded model is 3.6 AUROC points worse. One registered bound was not met and one was. The paper, abstract, limitations and ledger row V2-E19 say so. The maintainer note sent on 2026-11-23 may describe only the earlier gain: check its wording, and consider sending the new numbers.
3. **Independent application of the reporting standard: parked on 2026-11-26.** The rater document was sent and rating files came back whose authorship could not be established (one says an AI model filled it in). None is used, none is in the repository, and the paper keeps calling the standard unvalidated, so nothing in the manuscript depends on this. Reopen only with evidence that a person wrote the answers without AI, for example the editor's saved history of the file over time (in VS Code, the Timeline view of the file shows local history entries) or the full transcript of any cleanup chat. The authors' answers are in `pclCodebase/validation_share/`, and their hash is in `v2/validation_kit/AUTHORS_ANSWERS_HASH.md`.
3b. **Confirm the E15 outside coder before submission (this one is in the paper).** The paper says the coder used no language model for the labeling. Ask to see the version history of the coder's original document. If it does not show the labels being entered over time, either remove the E15 result or describe its authorship as unverified.
4. **Patient-level bootstraps.** The patient identifiers of the full MIMIC-IV and eICU-CRD cohorts are not on this machine. If you run on the machine that has the credentialed tables, a cluster bootstrap over patients for the whole-cohort kappa and the audit draws would replace the stay-level intervals. The paper states the limit.
5. **Maintainer replies.** Two of three maintainers were notified on 2026-11-23. Add a sentence if one replies.
6. **Rewrite the passages in `v2/AUTHOR_PASS.md`** in your own voice, keeping the numbers.
7. **Read the final PDF end to end**, and decide whether to submit.

## Done in this pass

- Retitled twice. Current title: "Clean Verdicts Without Evidence: An Audit of Five Clinical Confound Detectors" (the first retitle, "Can This Check Fail?", promised a sensitivity test that the paper does not run). The failure modes are now silent pass (undefined-input pass and weak-control pass) and threshold sitting. The two development hazards moved to the limitations.
- E17 (addendum 9): executed degenerate-input test of the five detectors, 19 of 27 undefined cells return a clean verdict. This is now the headline evidence and replaces the rubric-counted prevalence.
- E18 (addendum 10): the point rule against an interval rule and a bootstrap zone rule on 90 pair and database combinations, the interval rule never resolving the primary control, and prevalence-adjusted kappa.
- E16 (addenda 7 and 8): detector 2 near-threshold readings with 20 seeds; two verdicts changed.
- Detector 2, detector 3 outside its home idiom, and the repository reading moved to appendices. The main text ends on page 11.
- Detector table added to Section 4. Tables for E17 and E18 added to the main text and the appendix. Figure 4 label fixed.
- The loader paragraph now says our model is the benchmark's default `histgbm` configuration (library defaults). The remaining differences are the data file, the domain split and the feature discretization.
- Code supplement rebuilt with the new scripts and results (108 tests pass, 7 skip).
- A fresh-eyes mock review of the restructured text (recommendation: major revision) led to these fixes: the title and abstract now say the test checks one necessary condition and not sensitivity; the interval-rule error figures are consistent (at most 2.3% in the size simulations, 0.8% at n=500 over 2,000 audits, and described as against the whole-cohort verdict because the control's cohort interval contains the cutoff); the settling size and the no-resolution statement are reconciled; 5 degenerate-by-convention cells are split out (14 of 22 remain silent passes, post hoc); the pooling statement is scoped to the internal validation cases; the detector-code date claim replaces the unverifiable "did not change" claim (no detector commit after 2026-10-15, first v2 specification 2026-11-03); the primary control, home idiom and weak-control wording are defined where first used; the loader case is labeled a data-loader line; the narrow-reading count of 4 (3 without the divergence check) is stated; the four-fifths and detector 5 illustrations are one sentence in the main text.

## Deviations to know about

- Addendum 9 said cells would not be pooled across detectors, but the paper reports 19 of 27 with a descriptive interval. The paper says the interval treats the cells as independent although they are not.
- The E17 input list was written after reading the detector code, so the outcomes are not blind. The paper says so.
- Addendum 10's zone rule uses 200 audits for six pairs, and the interval rule's standard error is an approximation checked against a bootstrap on 100 audits.

## Reviewer points not addressed

- The mock reviewer's most valuable single change: an independent replication of both failure modes on diagnostics other groups wrote. The executed fuzz of 13 public checks and the validation kit are the partial answer; a wider fuzz (more libraries, the same input list) is the cheapest extension and has not been run.
- Replacing the primary control with a defensible negative control (a pair that experts accept as interchangeable with kappa well above 0.60), or an equivalence-test design, would remove the objection that the whole-cohort verdict is a point estimate on the threshold. It needs a new labeling choice and was not run.
- Sensitivity of the detectors is measured only by one to eight internal cases each (Appendix Table 19).
- Citations the reviewer suggested and I could not verify: Schuirmann 1987 (equivalence testing), Ethayarajh 2020, Cherian and Candes, Snoek et al. 2019. Not added.
- Independent coding of all 88 sites by two humans, and pinned model snapshots for the language-model raters. The paper no longer reports a prevalence, and states both limits.
- Equivalence-test or dose-response controls for detector 1 (a new design, not run).

## Tooling

- `paperlint.py` v3 is extracted from the skill and verified (hash 2b87a01d49cc2ae3...). The skill file on disk had doubled backslashes inside the code block, so I reversed that escaping before the hash matched. Remaining lint items: 30 "number not in ledger" (rounding, table widths, hash prefixes, repository line numbers, "AI Fairness 360"), file names in appendix site locations, number walls in appendix text, and benign word matches.
- The AAAI-format paper in `cane_ai/` is stale (five-seed numbers, old title) and should not be used.
