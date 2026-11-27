# Paper check, 2026-11-27 (audit only; the manuscript was not edited)

PDF checked: `v2/paper/main.pdf`, 30 pages, source `main.tex`. Three passes: a mock TMLR review, a cold read by a separate
model instructed to read like a first-year student (it saw only the PDF), and the `ml-paper-writer` linter and citation check.
The cold reader is a model playing a role, not a person, and does not replace a human reader.

Line numbers refer to `v2/paper/main.tex`.

## Verdict

**Not ready to submit. Mock TMLR recommendation: major revision.** The two core observations are believable (five entry points
lack input guards; a kappa on its cutoff gives an unstable subset verdict). The paper states some things its own evidence
does not support, still shows numbers that do not reproduce, and is too hard to read.

## P0: wrong or unsupported, fix before anything else

| # | Where | Problem | Fix |
|---|---|---|---|
| 1 | Abstract, l.30 | "a 500-stay audit flags between 41% and 49% of the time". At 500 stays the rate is about 48%. 41% to 49% is the range over audit sizes 100 to 5,000 (l.200, l.701; `e3_d1_audit_size.json`). | State one rate at 500, or give the range with its audit sizes. |
| 2 | l.191, Table 3 (l.220) | The rate at 500 stays appears as 48.4% (text) and 47.6% (Table 3); E3's observed rate is 48.7%. These come from different sets of 2,000 draws or a different run, and the paper does not say so. | Quote one primary value and say where the others come from. |
| 3 | Abstract and the loader paragraph in 5.2 | The loader numbers come from E19, one unseeded fit that does not reproduce. In E19b the reported accuracy gap has an interval above zero in only 6 of 10 seeds. | Replace with E21 (or E19b). Delete "reported accuracy is 2.0 points higher". Keep: 72% of rows labeled 0; true-label AUROC lower in all seeds. |
| 4 | Abstract against 5.2 (near l.184) | The abstract says the pattern "also appears in 5 of 22 undefined cells" of the fuzz. The body says these are "not five confirmed undefined-as-clean defects". | Use the body's wording, or drop the fuzz from the abstract (E23 replaces it as external evidence). |
| 5 | Broader impact against the repository section | One place gives the maintainer notification date (2026-11-23); another says issue dates are withheld for anonymity. | Pick one. Removing the date is the safer choice. |
| 6 | l.274 | The AI-use statement is a blank comment. TMLR asks for LLM use to be stated. | Only the authors can write it. |
| 7 | l.108 and the appendix | "13 specification documents" and the table of documents are out of date; there are now addenda up to 17. "Each experiment ... was specified ... before it ran" must be read against `v2/EXPERIMENT_STATUS.md`. | Update from that table. |
| 8 | Repository appendix | "undisclosed contamination was absent from 0 of 23" says the opposite of what is meant. | Goes away with the planned cut; otherwise "found in 0 of 23". |

## P1: what stops a reader (both the review and the cold read)

1. **The abstract is unreadable on first pass.** "Cells", "benchmark loader", "completion rate", "kappa", "500-stay audit",
   "interval rule" and "fuzz" arrive undefined. The loader sentence mixes two metrics, two test sets and a parenthesis.
2. **No worked example.** One short example would carry the paper: empty audit, kappa is NaN, `NaN < 0.60` is false, verdict "clean".
3. **Section 3, "Margins and controls".** A control is called "discriminating" in one sense and "uninformative" in another;
   the reader could not tell the two apart. "Negative control" is never shown by example, and nothing says early why the
   primary pair *should* be clean.
4. **The consequence is missing.** No result shows that one of the silent-pass inputs occurs in a real run. Say so plainly,
   up front, and let the loader case and E23 carry the practical claim.
5. **Detector failures are too quiet.** That detector 5 misses its only internal positive, and that detector 3 recognizes
   nothing outside the authors' naming style, belong in the main text where the detectors are introduced.
6. **Three decision rules are defined apart** (the zone rule appears after the figure and table). Define them together.
   Table 3's caption does not say what m is or whether the primary control is inside the m <= 1.64 row.
7. **Where the reader would stop:** in 5.2 at "We then compared this unguarded pipeline", then certainly at the repository
   counts. Give the loader comparison one small table. The planned cuts remove the repository counts.
8. **Defensive writing.** Most results end by taking themselves back. State each limit once, in Limitations.
9. **Lab-notebook detail** in text and appendices: commit hashes, commit dates, processor types, seed numbers by machine,
   22 script or file names (linter).
10. **Length and leftovers.** 30 pages. Two appendices ("Detector 1 controls", "The fuzz cells") are a heading and a table
    with no text. The four-fifths appendix introduces its 133 cases and states "93 of 133 (0.614 to 0.776)" twice. The
    agreed cuts (repository reading, outside coder, raters, detector 2 and 5 detail,
    four-fifths) are not yet applied.

## Reviewer's substantive concerns (TMLR criteria)

- **Are claims supported?** Not yet: see P0. After those fixes, the supported claims are narrow.
- **Would anyone care?** The narrow claim about the authors' own five detectors is weak on its own. External evidence is what
  makes it matter. Today that is one loader line and a debatable fuzz. **E23 decides this paper's strength**, and must be
  reported whatever it shows.
- **Threshold sitting** reads as expected sampling behavior shown on one pair. Present it as an illustration with a
  measurement, not as a second discovery. The interval rule mostly declines to decide, and the text should lead with that.

## Linter and citations

- Linter (both ledgers): 39 numbers without a matching ledger entry, 55 warnings, 2 notes. Most unmatched numbers are table
  cells, counts, version numbers and identifiers; each still needs a ledger row or removal after the rewrite. Warnings:
  number-dense passages, file names in the text, tool names (expected in the rater sections, which are being cut), and
  eight citations checked only at the metadata level but attached to sentences that describe their content.
- Citations: 49 cited, 49 in the bibliography, all with a ledger row. One extra ledger row (Schuirmann 1987) is checked at
  abstract level and not yet cited.
- Prose measures are inside the human range (mean sentence length 23 words, no density flags). The reading problem is
  structure and density of ideas, not word choice.

## Order of work for the rewrite

1. Apply the agreed cuts. 2. Insert E21 and E23. 3. Rewrite the abstract, Section 3 and the start of Section 6, with the
worked example. 4. Fix P0 items 1, 2, 4, 5, 7. 5. Move limits to one place. 6. Rebuild, lint, and run one more cold read.
7. The authors add the AI-use statement, rewrite their passages and read the whole PDF.
