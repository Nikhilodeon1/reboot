Points in the order of the review.

**Baselines only for detector 2; validation depth is uneven (N1).** Accepted. Table 2 is now a validation-depth matrix: for each detector, the positives and controls internal and external, how many controls can fail by our margin rule, the external ground truth, the uncertainty measure, and the baseline and manual-label coverage. The baselines we have:
- Detector 1: a cross-site prevalence-ratio check. It is inverted. It ranks legitimate cross-site comparisons above real label mismatches (AUROC for picking out mismatches {{N:prev_auroc_demo}} at demonstration scale and {{N:prev_auroc_full}} at full scale).
- Detector 2: three standard checks, on the same trained models (below).
- Detector 3: the tool of Yang et al., built after three environment changes. It reports nothing on both fixtures and recognises no train/validation/test pairing, so it does not apply to our idiom.
- Detector 4: two literature searches found no baseline. We did not invent one.
- Detector 5: out of scope. The naive cross-site gap is the quantity detector 5 decomposes, so it is an input to the detector, not an independent check.

**Baseline and main analysis at different scales (N2).** Accepted and fixed. The baselines now run on the same trained models, stays and seeds as detector 2, at demonstration scale and at full scale (MIMIC-IV to eICU). At demonstration scale: {{N:base_demo}} flags at 0% leakage. At full scale (flags out of 5 seeds at 0, 5, 20, 100% leakage): {{N:base_full}}. None carries information about this scenario, in different ways at the two scales. We do not claim detector 2 beats them, because a corpus-size control recovers {{N:r2r1_full5}} and {{N:r2r1_full20}} of its effect at full scale. Downstream AUROC does not move at full scale ({{N:fs_auroc}} at 5, 20, 100% leakage; gap at 0% {{N:fs_gap}}). On a large held-out demonstration target the change is {{N:a5p_d5}}. The earlier signal-to-nuisance ratio and the downstream-direction sentence are removed.

**Result order does not follow method order (N3).** Accepted. Sections now follow the order: detectors and protocol, internal validation, catalogue, evidence per type in type order, external generality, baselines. Internal audit and catalogue definitions are separate sections.

**Summary describes the paper as pipeline-shift detection (N4).** We do not dispute the summary. We have clarified the contribution in the introduction and the global comment. The paper is a critique, with negative results, of verification tooling: five detectors were built, and the audit of those detectors is the contribution. It is not a method for detecting dataset shift.

Please see the global comment for the corrections to our own claims, which affect Table 1 and the baseline section.
