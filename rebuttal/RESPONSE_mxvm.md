Points in the order of the review.

**Limited external validation, small and correlated cases (M1).** Conceded. Table 1 now reports per-detector counts with exact intervals and a pooled row marked reference only. Table 2 gives the validation depth per detector: positives and controls internal and external, the number of controls that can fail by our margin rule, external ground truth, uncertainty and baselines. For detector 1 at full scale, one of six controls is discriminating (margin 0.06) and five are ceiling controls (for example 5.39 for eICU). Detector 4 has no external positive. Section 10 states these limits.

**Detector 5 fails its positive; detector 3 has no coverage; detector 2 is confounded (M2).** We agree these are findings, and we added data to each.
- Detector 5: the flagship composition ratio straddles the gate, flagged 2/5 at n = 1200 and 0/5 at n = 4000, and 3/5 at n = 900 and 1500. A normal approximation gives flag probabilities of about 0.42 and 0.15 at the first two sizes, consistent with the counts (five seeds per cell; the same seeds supply estimate and count). Restricted to two shared components it flags 5 of 5 but is unstable on its control. On external data, five seeds: precision 9/9, false-positive rate 0/10.
- Detector 3: 0 contaminated, 1 disclosed oracle, 1 ambiguous, 21 sound and 30 not selections among 53 hand-labelled sites, so sensitivity is undefined. The detector returned indeterminate on 53 of 53 files.
- Detector 2: at full scale a corpus-size control recovers 0.55 and 0.69 of the effect, above our pre-registered line of 0.5, so by our rule the effect is confounded with corpus size. At demonstration scale the ratios were 0.31 and 0.48. The detector is unchanged. Its 0% control compared an arm with itself, so we added a 20-replicate null: 1 of 20 flagged (exact interval 0.001 to 0.249).
These are reported as results of the audit, not as defects we repaired.

**Stronger external validation (M3).** Partly met. Type 1 now has a 25-repository read with exact intervals (4/48 (exact 95% interval 0.023 to 0.200) on the narrow reading; 16/48 (0.204 to 0.484) on the broad). Baselines were rerun on the same trained models at both scales (Section 8). We did not obtain external instances of Types 2 to 4, and the paper says so in Table 3 and Section 10.

**What was not run.** Missingness arms at full scale, because the available caches lack the raw series. No GPU work, because the credentialed data stayed on one author's machine.
