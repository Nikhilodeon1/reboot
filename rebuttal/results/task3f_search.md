# Task 3f: live search for other baselines

Run 2026-10-08, web search, standard mode, results as returned. Novelty claims
in the response may not exceed what these searches support.

| Query | Result |
|---|---|
| static analysis detect model selection leakage test set reuse hyperparameter tuning machine learning code | Returned Yang et al. (ASE 2022) and tools built on its categories (overlap, pre-processing, multi-test), plus a learning-based detector. No source was found that targets selection on a held-out or out-of-distribution split as a distinct confound. Multi-test leakage is the nearest category. The search summary itself said it did not confirm that the detector models hyperparameter loops. |
| detecting target leakage derived feature computed from label static analysis data science code circular feature | Returned Yang et al. and Subotić, Bojanić and Stojić (SOAP 2022). Neither addresses a feature whose computation uses the target or a quantity derived from it. Nothing found for detector 4's circular-derived-variable problem. |

## What this supports

- Detector 3: Yang et al. is the adjacent published tool, and it was run (see
  `task3f_yang.md`). It reports nothing on both fixtures and recognises no model
  pairing in either.
- Detector 4: **no baseline was found in two standard-mode queries.** The
  defensible statement is "we did not find one", not "none exists". No baseline
  was invented.
- Two searches are a thin basis. Extended-mode searching or a literature survey
  could still surface prior work, so any claim of novelty should be worded as
  "to our knowledge, after the searches recorded here".
