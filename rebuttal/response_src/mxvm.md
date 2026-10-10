Points in the order of the review.

**Limited external validation, small and correlated cases (M1).** Conceded. Table 1 now reports per-detector counts with exact intervals and a pooled row marked reference only. Table 2 gives the validation depth per detector: positives and controls internal and external, the number of controls that can fail by our margin rule, external ground truth, uncertainty and baselines. For detector 1 at full scale, one of six controls is discriminating (margin {{N:d1_m_mimic}}) and five are ceiling controls (for example {{N:d1_m_eicu}} for eICU). Detector 4 has no external positive. Section 10 states these limits.

**Detector 5 fails its positive; detector 3 has no coverage; detector 2 is confounded (M2).** We agree these are findings, and we added data to each.
- Detector 5: the flagship composition ratio straddles the gate, flagged {{N:d5_1200}} and {{N:d5_4000}}, and 3/5 at n = 900 and 1500. A normal approximation gives flag probabilities of about {{N:d5_pred1200}} and {{N:d5_pred4000}} at the first two sizes, consistent with the counts (five seeds per cell; the same seeds supply estimate and count). Restricted to two shared components it flags 5 of 5 but is unstable on its control. On external data, five seeds: {{N:d5_ext}}.
- Detector 3: {{N:t3_labels}} among {{N:t3_sampled}} hand-labelled sites, so sensitivity is undefined. The detector returned indeterminate on {{N:t3_indet}} files.
- Detector 2: at full scale a corpus-size control recovers {{N:r2r1_full5}} and {{N:r2r1_full20}} of the effect, above our pre-registered line of 0.5, so by our rule the effect is confounded with corpus size. At demonstration scale the ratios were {{N:r2r1_demo5}} and {{N:r2r1_demo20}}. The detector is unchanged. Its 0% control compared an arm with itself, so we added a 20-replicate null: {{N:null_flags}} flagged (exact interval {{N:null_ci}}).
These are reported as results of the audit, not as defects we repaired.

**Stronger external validation (M3).** Partly met. Type 1 now has a 25-repository read with exact intervals ({{N:t4_narrow}} on the narrow reading; {{N:t4_broad}} on the broad). Baselines were rerun on the same trained models at both scales (Section 8). We did not obtain external instances of Types 2 to 4, and the paper says so in Table 3 and Section 10.

**What was not run.** Missingness arms at full scale, because the available caches lack the raw series. No GPU work, because the credentialed data stayed on one author's machine.
