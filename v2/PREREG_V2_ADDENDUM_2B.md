# Pre-registration, v2, addendum 2b: three external language-model raters and an adjudication rule

Committed before any output of the external raters exists. It extends addendum 2.

**What happened before this addendum, stated so that the order is clear.** The in-session rater for sheet A (53 model-selection sites) wrote its file
before its session ended. We analysed it once with `e7_agreement.py`: 42 of 53 labels agree (exact 95% interval 0.659 to 0.892), kappa 0.636. The
rater labels 2 sites CONTAMINATED where the committed labels have none. The authors then read those two sites (robustdg `slab-tune.py` and eICU-GNN-LSTM
`train_ns_lstmgnn.py`) and recorded what they found (below). The rater for sheet B (88 reachability sites) did not finish and is being rerun. Everything in
this addendum that concerns the external raters was fixed after seeing those first results and before any external output exists.

**Raters.** (R0) the in-session instance, which had read access to the pinned repositories. (R1 to R3) three external models chosen by the owner and named
by the owner: Claude Opus 5.5, Gemini 4 argon and ChatGPT 5 luna, each in a fresh chat with no other context. The owner records the exact model names and
dates. Each external rater receives only `rater_sheet_*_ctx.md` (the matched lines with up to 30 lines of context each side) and the prompt in `PROMPT_*.txt`
(the committed rubric and the response format). External raters cannot open the repositories. That is a difference in information from R0 and is reported as such;
it will push external raters toward AMBIGUOUS or undecidable more often than R0 or the committed labels.

**Analysis (`e7_validate.py`, `e7_agreement.py`, `e7_combine.py`).** Per rater, per sheet: raw agreement with the committed labels with an exact interval, and kappa.
Pairwise kappa between raters. The majority label of the three external raters (ties go to AMBIGUOUS for sheet A and NOT_APPLICABLE for sheet B). The registered reading
rule uses the median kappa across all raters that returned a complete file: below 0.60 the external counts are called rubric-dependent and reported as a range across raters;
at 0.60 or above the paper reports the agreement and says the counts are stable to the rater. A rater's incomplete or invalid file is reported and excluded.

**Adjudication rule, fixed now.** The committed labels were fixed before the detector ran and stay the primary result. For every site where the majority of raters
(including R0) disagrees with the committed label, and the label change would alter a headline count (a CONTAMINATED site, or a REACHABLE_UNGUARDED site under
either reading), the authors read the file and record the evidence and a judgement (committed label correct, committed label wrong, or unresolved). The paper then reports
the registered counts and the counts after adjudication side by side. A committed label that the authors judge wrong is disclosed as an error, not silently replaced.

**Authors' reading of the two disputed sheet-A sites, recorded now.**
- robustdg `reproduce_scripts/slab-tune.py` lines 85 to 88 (committed SOUND, R0 CONTAMINATED). The script picks the best hyperparameter file by the value on the line
  `data[-4]`, commented "Source validation accuracy". In `train.py` that line prints `final_accuracy_source_val`, which is `train_method.final_acc[idx]`, the test-domain accuracy at
  the epoch chosen by source validation accuracy. The sweep therefore maximizes a test-domain accuracy across hyperparameters. We judge the committed label wrong.
- eICU-GNN-LSTM `train_ns_lstmgnn.py` line 179 (committed NOT_SELECTION, R0 CONTAMINATED). The class sets `eval_mask = val_mask if eval_split == 'test' else test_mask`,
  which looks like swapped masks. Whether the learning-rate schedule or the reported split is affected depends on how `eval_split` is set at call time, which we did not run.
  Unresolved.
