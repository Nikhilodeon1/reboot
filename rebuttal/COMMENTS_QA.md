# QA for the OpenReview comments (text only)

Built by `python rebuttal/scripts/build_comments.py` from `rebuttal/comments_src/*.txt`; the final texts are
in `rebuttal/comments/`; every number is listed with its ledger row, source file and commit in
`rebuttal/RESPONSE_NUMBERS_CHECK.md` (ledger ids appear only there). Raw review text:
`C:\Users\nikhi\Downloads\Auditing the Auditor_ ... OpenReview.pdf` (text extracted and read in full).

## Flags before posting

1. **Spot-check.** Filled: 8 of 12 labels agree (exact 95% interval 0.349 to 0.901); see `rebuttal/results/spotcheck_agreement.json`. Owner must confirm who produced the second set of labels, because the comments say "an author who had not seen our labels".
2. **Length limit.** Assumed 5,000 characters per comment. [OWNER: fill in the real limit.] Longest: 4,526.
   The global comment is already two numbered parts.
3. **The mirror must be refreshed before posting.** The mirror (anonymous.4open.science/r/reboot-8568/) lists
   only `.gitignore, CONTRIBUTORS.md, README.md, TAXONOMY.md, config.py, detectors, requirements.txt, scripts, src`.
   It has no `rebuttal/` and no `docs/`. Global part 2 says the rebuttal directory holds the pre-registration documents,
   the ledger and the result files, so that sentence is false until the mirror is refreshed.
4. **Intervals.** Proportions use exact Clopper-Pearson intervals throughout. The AUROC-change intervals quoted for the
   held-out target and at full scale are t-intervals on a mean difference over 5 seeds (df 4), a different quantity; the
   comments call them intervals without naming a type. Wilson figures appear nowhere.

## Length and grep results

| Comment | Characters |
|---|---|
| 0a global, part 1 (Corrections) | 4,526 |
| 0b global, part 2 (what we ran, planned revisions, fit) | 4,037 |
| 1 JJvk | 3,974 |
| 2 hDMD | 4,061 |
| 3 mxvm | 3,264 |
| 4 Npus | 3,516 |
| 5 nyqg | 3,805 |

QA grep on every comment (built into the script): `validated`, `FPR 0`, `worse with data`, `order of magnitude`,
`expected direction`, `renders a verdict`, em dashes, `see the revised PDF`, `now says`, flattery phrases: no hit.
The retraction of the "worse than at 1/640th the data" statement is quoted with different words on purpose.
No table syntax. No ledger id in any comment. Tense: what we ran is past; paper changes are "we will". The three
replacement sentences (abstract, catalogue rescoping, detector 2 scope) are quoted verbatim in global part 2.

## Anonymity and mirror check

Nothing in the comments names or hints at the authors. Findings about the repository, for the owner to decide:
- **Mirror contents.** `CONTRIBUTORS.md` in the mirror has no names. It says development used Claude (Anthropic) as an
  assistant, and that the history was exported without development history. It also still says detector 1's full-scale
  figures are transcribed, which is now out of date (they were regenerated and archived); update it when refreshing.
- **Commit history.** The mirror has no history, so the comments do not claim the commit order is checkable there; they
  point to the documents that carry the hashes and times. The paper's appendix lists the first two hashes and the
  anonymized patches are in `detectors/preregistration_evidence/`.
- **GitHub repository.** The source repository is public (an unauthenticated clone worked) under the author's handle, with
  55 commits by that handle. This is outside the mirror, but anyone who finds the GitHub URL sees it. Consider making it
  private until review ends.
- **Internal files.** `rebuttal/REPORT_FOR_STRATEGY.md`, `REPORT_2_FOR_STRATEGY.md` and `USER_SPOTCHECK.md` do not name
  anyone but read as internal working documents; exclude them from the mirror (4open.science lets you ignore paths).
- A scan of every tracked file in the repository for the identifying strings the owner keeps in a local list found 0 hits.
- The OpenReview page the owner saved shows the owner's name in its header; nothing from the page except the review text
  was used.

## What the comments cite, and whether it exists in the mirror today

Mirror root URL: exists. "Rebuttal directory (pre-registration documents, ledger, result files)": will exist after
refresh, not today. Detector fixtures, `detectors/results/`, `TAXONOMY.md`: exist today. No paper section is cited
as "now says"; the submission's own section numbers are not used. New citations: Yang et al. only, which is in
`CITATIONS_VERIFIED.md`.

## Deliberately not in the comments

The manuscript rewrite is deferred (OpenReview takes text only). Items from the earlier package that depend on a revised PDF
(`CHANGED_CLAIMS.md`, `QA_REPORT.md`, `manuscript/`) are kept but not used here.
