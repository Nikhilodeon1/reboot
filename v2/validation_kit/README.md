# Applying the reporting standard to external diagnostics

Purpose: test whether a person outside the author group reads the five reporting items the same way we do. About two hours per rater for three diagnostics.

## For the authors (before sending anything)

1. Fill `answers_authors.csv` (copy `answers_template.csv`) for the three diagnostics in `CASES.md`, from the documentation and the code of the versions you pin. Record the versions and URLs you used in the `evidence` column.
2. Commit `answers_authors.csv` and note the commit hash. Do not send it to the rater.
3. Send the rater `CARD.md`, `CASES.md` and `answers_template.csv` only. Do not send the paper, the ledger or this README.

## For the rater

Read `CARD.md`. For each diagnostic in `CASES.md`, find the official documentation and, where the card asks, the source code. Answer the five items in `answers_template.csv` with one of the allowed codes, and paste the evidence (a URL and a line or sentence) in the `evidence` column. If you cannot tell, write `unclear` and say what you looked at. Use no language model for the answers. Note your own background (for example, years of experience with Python and ML) in `rater_background.txt`.

## Scoring

`python v2/validation_kit/score_agreement.py answers_authors.csv answers_rater.csv` prints per-item agreement, overall agreement and Cohen's kappa over the items answered by both, and lists the disagreements. Report the numbers whatever they are. The paper may say that a second person applied the standard only after this has been run.

## Data handling

No patient data is involved. The diagnostics are public libraries, read through their own documentation and code.
