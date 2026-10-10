# Issue matrix

Reviewer ids: J = JJvk (4), H = hDMD (3), M = mxvm (3), N = Npus (2), Y = nyqg (3); Q = a question.
Manuscript locations refer to the revised `main.tex` (section numbers, Table 1 = internal suite,
Table 2 = validation depth, Table 3 = evidence strength, appendices A to E). Response locations
name the file. The wording of the points is from the matrix in the writing prompt; the raw review
text (`rebuttal/reviews_raw.md`) was not in the repository when this was written, so each row
must be checked against it before submission.

| ID | Point | Stance | Manuscript location | Response location |
|---|---|---|---|---|
| J1 | Types unevenly supported; catalogue not shown general or complete | Concede, rescope | Abstract; Sec 1; Sec 5 (stage model, uncovered classes); Table 3; Sec 10 | RESPONSE_JJvk |
| J2 | Same group built and audited; detector 3 scan shows non-generalization | Concede, add checks | Sec 7.1 (53 hand-labelled sites); Sec 10 | RESPONSE_JJvk; GLOBAL |
| J3 | Detector 3: no evidence on sensitivity to the target problem | Answer with data | Sec 7.1; Table 2 | RESPONSE_JJvk |
| J4 | Detector 2 cannot separate values from missingness; detector 5 components analogous | Answer with data | Sec 6.1 (detector 2 paragraph); Sec 6.3 | RESPONSE_JJvk |
| J5 | Weight on internal precision and recall | Concede | Abstract; Table 1 | RESPONSE_JJvk |
| JQ1 | Comprehensive or initial taxonomy? | Initial | Sec 5 first paragraph; Abstract | RESPONSE_JJvk |
| JQ2 | Manually review a subset of repos | Done | Sec 7.1 | RESPONSE_JJvk |
| JQ3 | How much will the detector 2 result change? | Pre-stated prediction and result | Sec 6.1 | RESPONSE_JJvk |
| JS | Make failure analysis the headline | Accept | Abstract | RESPONSE_JJvk |
| H1 | No formal definitions or completeness argument | Accept | Sec 5 | RESPONSE_hDMD |
| H2 | Generalization with three repos; failure modes not reproducible | Accept in part: external evidence supports Type 1 only | Sec 7.2; Table 3; App E | RESPONSE_hDMD |
| H3 | Aggregates lack intervals and pool heterogeneous detectors | Accept | Table 1; Abstract | RESPONSE_hDMD |
| H4 | Separate internal audit from the catalogue | Accept | Sec 3 to 7 order | RESPONSE_hDMD |
| H5 | No consequence shown outside own repo | Accept in part | Sec 7.2 (DomainBed); repo `results/task4f_demo_output.txt` | RESPONSE_hDMD |
| H6 | Develop with domain experts | Acknowledge as future work | Sec 10 | RESPONSE_hDMD |
| H7 | Better suited to case-report format | Receptive | Not in manuscript | RESPONSE_hDMD; GLOBAL |
| M1 | Limited external validation; tiny correlated cases | Concede | Table 1; Table 2; Sec 10 | RESPONSE_mxvm |
| M2 | D5 fails positive; D3 no coverage; D2 confounded | Reported as findings; data added | Sec 6.1, 6.3, 7.1 | RESPONSE_mxvm |
| M3 | Wants stronger external validation | Partly met | Sec 7, Sec 8 | RESPONSE_mxvm |
| N1 | Baselines only for D2; uneven validation depth | Accept | Table 2; Sec 8 | RESPONSE_Npus |
| N2 | Baseline and main analysis at different scale | Accept | Sec 8; App D | RESPONSE_Npus |
| N3 | Result order does not follow method order | Accept | Sec 3 to 8 order | RESPONSE_Npus |
| N4 | Summary describes the paper as pipeline-shift detection | Do not argue | Sec 1 (contributions) | RESPONSE_Npus; GLOBAL |
| Y1 | Headline rests on 6 TP and 12 TN | Concede | Abstract; Table 1 | RESPONSE_nyqg |
| Y2 | "Every type has a measured failure" too strong | Concede | Abstract; Sec 5; Table 3 | RESPONSE_nyqg |
| YQ1 | What evidence shows Type 4 as an observed failure? | Answer honestly: counterfactual | Sec 6.4 | RESPONSE_nyqg |
| YQ2 | When is a threshold or control clinically meaningful? | Answer | Sec 6.2 | RESPONSE_nyqg |

Unmapped rows: 0 of 26. Rows to verify against the raw text: all 26.
