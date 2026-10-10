Points in the order of the review.

**No formal definitions or completeness argument (H1).** Accepted. Section 5 now gives a stage model of a diagnostic and a predicate for each type. Type 1a: the verdict function is total where the statistic is partial. Type 1b: a control whose margin to the boundary exceeds 3 standard deviations, so it cannot fail. Type 2: for two implementations a domain convention treats as interchangeable, the population value of the statistic lies within one audit standard deviation of the threshold. Types 3 and 4 follow the stage they fail at. Completeness is claimed only against the stage model, and the section lists what the catalogue does not cover. The definitions were written by us and have not been reviewed by outside experts.

**Generalization with three repositories; failure modes not reproducible (H2).** Accepted in part. We extended the Type 1 read to 25 repositories (the 18 from the detector 3 scan, AIF360 and six new ones chosen by a star-ranked rule fixed before any query), with patterns frozen first and 88 sampled sites labelled by a rubric committed before reading. Reachable and unguarded in {{N:t4_narrow}}, or {{N:t4_broad}} if NaNs that arise only from diverged training count. We did not fix that convention in advance. The four positives are listed with file, line and commit in Appendix E. The external evidence supports Type 1 only, and the paper now says so.

**Aggregates lack intervals and pool heterogeneous detectors (H3).** Accepted. Table 1 reports per-detector counts with exact intervals. The pooled row is reference only ({{N:pool_prec}}, {{N:pool_rec}}, {{N:pool_fpr}}), and the abstract no longer uses it. One interval type (Clopper-Pearson) is used throughout.

**Separate the internal audit from the catalogue (H4).** Accepted. The paper now runs: detectors and protocol (Section 3), internal validation (Section 4), the catalogue (Section 5), evidence per type (Section 6), external generality (Section 7). Results follow the order of the definitions.

**No consequence outside our own repository (H5).** Accepted in part. For the DomainBed fragments we ran the verbatim lines on synthetic inputs: a NaN listed first wins the selection, a NaN listed later is ignored, and a NaN or empty list passes the guard. The repository holds this output. It shows the semantics of the pattern, not a bug in shipped DomainBed, which cannot reach these inputs with its shipped datasets. We kept "structurally present, not currently exploitable."

**Is the pattern concentrated in verdict code?** We computed the split. Under the narrow reading it is {{N:t4_split_narrow}}, and under the broad reading {{N:t4_split_broad}}. The direction reverses with the convention, so we found no evidence of concentration. The earlier argument that the pattern concentrates in verdict code is removed.

**Domain experts (H6).** Acknowledged as future work. The definitions and the catalogue would benefit from review by clinicians and statisticians who build diagnostics, and we welcome specific suggestions. Section 10 says so.

**Case-report format (H7).** We are receptive. Types 2 to 4 are narrower evidence than a general catalogue needs, and a critique format would suit them.
