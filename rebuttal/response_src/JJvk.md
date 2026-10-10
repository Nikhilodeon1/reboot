Points in the order of the review. Locations refer to the revised manuscript.

**Types unevenly supported, not shown general or complete (J1, Q1).** Conceded. The catalogue is initial, not comprehensive. Section 5 now defines four stages of a diagnostic (statistic, decision rule, controls, design process), puts each type at one stage, and claims completeness only against that stage model. It lists classes the catalogue does not cover. Table 3 states the evidence per type: Types 1 to 3 have measured instances in our detectors, Type 1 also has an external structural instance, and Type 4 is counterfactual.

**Same group built and audited; the detector 3 scan (J2, Q2).** Conceded, and we added checks. We hand-labelled {{N:t3_sampled}} candidate selection sites from the 18 repositories, using patterns frozen before the scan and a rubric committed before any site was read or the detector was run on it: {{N:t3_labels}}. An independent spot-check of 12 sites by an author who had not seen our labels: {{SPOTCHECK}}. Section 10 says what these checks do not fix.

**Detector 3 and the target problem (J3).** Sensitivity is undefined, because the sample contains no contaminated site: undisclosed contamination in {{N:t3_cp}} real selection sites. The detector returned indeterminate on the files of {{N:t3_indet}} sites, so it makes no clean verdict either. Yang et al.'s tool, built after three environment changes, reports nothing on both fixtures and recognises no train/validation/test pairing. We now describe detector 3 as a guard for one's own sweeps, not a retrospective auditor (Section 7.1).

**Detector 2, values versus missingness; detector 5 components (J4, Q3).** Our pre-stated prediction was a mixed result with the missingness share R between 0.25 and 0.6. On the demonstration pair R was {{N:R_demo}} at 5% and 20%: values-dominated by the pre-registered rule, so the prediction was wrong. The mask-transplant arm is under-filled ({{N:fill_a3}} of cells observed against {{N:fill_target}} in the target), so a missingness contribution is not excluded. At full scale R is undetermined, because the available caches lack the raw series. The larger finding is that a pre-registered corpus-size control recovers {{N:r2r1_full5}} and {{N:r2r1_full20}} of the effect at full scale. Detector 5's component set is analogous, not identical. Restricted to the two shared components it flags its flagship in 5 of 5 seeds, but its ratio on the same-site control averages {{N:d5_control}} at n = 900, so the composition gate is unstable (Section 6.3).

**Weight on internal precision and recall (J5, headline suggestion).** Conceded and accepted. The abstract now leads with the failure analysis and no longer states pooled precision, FPR or recall. Table 1 gives per-detector counts with exact intervals, and the pooled row is marked reference only ({{N:pool_prec}}, {{N:pool_rec}}, {{N:pool_fpr}}). The abstract says in one clause that this is a critique, with negative results, of verification tooling.

**Question 1.** Initial, as above.

**Question 2.** Done, as above. The scan covers Python files only ({{N:t3_gap}}).

**Question 3.** The prediction was pre-registered and missed, and the corpus-size control changed the picture more than the missingness arms did. Both are in Section 6.1.
