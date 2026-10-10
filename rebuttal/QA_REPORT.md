# QA report for the revised manuscript and response drafts

Run 2026-10-10 16:22 local, first full draft. Commands: `python rebuttal/scripts/qa_check.py` and
`python rebuttal/scripts/build_response.py`. Both are deterministic and rerunnable.

## Open items that block submission

1. **`rebuttal/reviews_raw.md` is missing.** The reply drafts follow the point matrix in the writing
   prompt, and every row of `ISSUE_MATRIX.md` must be checked against the raw review text, including
   the order of weaknesses and questions and the wording of any quoted fragment. No fragment of
   review text is quoted in the drafts, to avoid misquoting.
2. **The spot-check line is a placeholder.** `{{SPOTCHECK}}` appears in `RESPONSE_GLOBAL.md` and
   `RESPONSE_JJvk.md` until the owner's 12 labels arrive (k of 12 with an exact interval, not a blind
   relabel).
3. **Portal facts to confirm:** whether a revised PDF can be uploaded during the response period, and
   the real character limit per comment (4,800 is assumed; the longest draft is 4,011).
4. The `IRB` wording in the manuscript still carries its original `TODO` comment (institutional
   confirmation needed). It was not changed.

## Gate 1: ledger check

Every number in the revised manuscript and in all six response drafts occurs in `LEDGER.md`, the
submitted manuscript or `numbers.json` (rounding allowed): **0 exceptions** after fixes. During the
check, 6 ledger rows were added because the text used values that were only in table files or in
hand-written status notes: `T1a-per-detector`, `A2-4c-positives`, `A3-cp-detector3`, `T2-fill`,
`T2-r2r1`, `FS-cohorts`. Every response number is also bound to one ledger row in `numbers.json`,
and the build fails if a number does not occur in its row.
Where the strategy-side figures differed from the ledger, the ledger was used:
- 0 of 23 detector 3 sites: exact upper bound **0.148** (the earlier 0.14 was a Wilson bound). All
  Wilson intervals are marked SUPERSEDED in the ledger and appear nowhere in the manuscript or
  responses.
- Detector 5 Type 2 predictions at n = 4000: **0.15** from the five-seed archive (mean 0.272,
  SD 0.027), not the 0.24 hand estimate that used three seeds.
- 5a-prime target size: 13,879 to 13,888 stays and 285 to 289 positives (not "13,880" and "287").

## Gate 2: self-audit of each new experiment (four items)

| Experiment | Undecidable count | Control margin | Uncertainty at the operating point | Decision rule provenance |
|---|---|---|---|---|
| Detector 2 demo arms (Task 2) | R defined at both levels (A1 minus A2 clears 2.132); 0 undecidable | not applicable (no threshold control) | t, df 4, 5 seeds | `25fc617` |
| Detector 2 full-scale arms | R undetermined (A3, A4 not buildable); stated | not applicable | t, df 4, 5 seeds | `4918770`, `69148a9` |
| 20-replicate null | 0 | not applicable | exact interval 0.001 to 0.249 | `d14687a` (reading fixed before running) |
| Detector 3 site review | 53 of 53 indeterminate at file level, reported, not folded into TN | not applicable (deterministic) | exact interval 0.000 to 0.148 (0/23) | `b845cc0`, `4c461eb`, `e82be15` |
| Type 1 extended read | 3 sites undecidable, counted as not applicable and noted | not applicable | exact intervals, both conventions | `bc365cf`, `073d042`, `879d885` |
| Baselines, same models (5a, full) | 1 of 5 undecidable AUROC seeds (gap) at demo; 0 at full scale | detector 2 and baselines have no margin | t intervals, exact flag intervals | `d14687a`, `69148a9` |
| 5a-prime | 1 seed with undefined in-domain AUROC (4 valid for the gap) | not applicable | t, df 4 | `d14687a` |
| Detector 5 (Task 6, per-seed archive) | 0 undecidable; 4 of 5 seeds at 95% ablation have HH absent on one side (availability infinite by construction) | control ratio unstable (reported) | exact intervals on flag counts | `25fc617`, `d14687a` |
| Detector 1 full-scale re-run | degenerate resamples are dropped by the shipped code (count not recorded) | margins computed for 8 cases (1 discriminating positive and 1 discriminating control) | 5000-resample bootstrap, audit draws | rule m <= 3 fixed in `25fc617` |

## Gate 3: anonymity

0 hits across the manuscript, the bibliography and every text file under `rebuttal/`, scanning for
home paths, email addresses, UUIDs and a list of identifying strings kept in a local file outside
the repository (so the check itself does not publish them). The only URL is the 4open.science
mirror. Pod and host names do not appear in any committed file.

## Gate 4: build

`main.tex` compiles to 9 pages in total, of which the main text ends on page 7, so the limit of 8
pages excluding references and appendices has at least one full page spare. Zero overfull boxes,
zero undefined references or citations. Three tables (internal suite, validation depth, evidence
strength) are in the main text; all other new tables are in the appendices. `main_latexdiff.pdf` was
built with `latexdiff-fast` (the standard script lacks a Perl module here), then three float-label
arguments that the tool had wrapped in change markup were unwrapped by hand so the diff compiles;
no content was changed.

## Gate 5: citations

Two new references, both verified against their pages on 2026-10-08 and recorded in
`CITATIONS_VERIFIED.md`: Yang et al. (arXiv:2209.03345, ASE 2022) and Subotic, Bojanic and Stojic
(SOAP 2022). No other reference was added. Two papers seen only in search snippets are not cited.

## Gate 6: response checks

| File | Characters | Placeholders | Open |
|---|---|---|---|
| RESPONSE_GLOBAL.md | 4,011 | 26 | SPOTCHECK |
| RESPONSE_JJvk.md | 3,363 | 15 | SPOTCHECK |
| RESPONSE_hDMD.md | 3,310 | 7 | none |
| RESPONSE_mxvm.md | 2,499 | 18 | none |
| RESPONSE_Npus.md | 2,991 | 9 | none |
| RESPONSE_nyqg.md | 3,104 | 11 | none |

No file is over the assumed limit; no em dash; no stock phrases; no unresolved placeholder other
than SPOTCHECK; no sentence asks for a score; the only track mention is the single Findings-fit
sentence in the global comment. Banned phrases checked in the manuscript and the responses:
none survive (`validated`, `FPR 0`, `worse with data`, `order of magnitude`, `expected direction`,
`renders a verdict`).

## Gate 7: claim ledger of changes

`CHANGED_CLAIMS.md` lists 27 weakened, reworded or removed claims with before and after text and the
ledger rows behind each; every row has an approval box for the owner.

## Deviations from the prompts, for the owner

- Placeholders use `{{N:key}}` bound to `numbers.json`, which names a ledger row for each entry,
  because the ledger values are descriptive strings rather than single numbers.
- The raw reviews were not available, so the replies are drafted from the issue matrix and not from
  the review text (see open item 1).
- The validation-depth matrix is a separate Table 2 in the main text (not merged with Table 1).
