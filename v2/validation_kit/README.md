# Applying the reporting standard to external diagnostics

Purpose: test whether a person outside the author group reads the five reporting items the same way we do. About two hours for the rater, for three diagnostics.

## For the authors, before sending anything

1. Fill the authors' answers (columns as in `answers_template.csv`) for the three pinned diagnostics in `CASES.md`, and have an author check every answer. Keep the file outside this repository until the rater has returned theirs, because the repository is public.
2. Record the SHA-256 of the authors' file in a committed note before the rater receives anything.
3. Build the rater's document with `python v2/validation_kit/make_rater_docx.py tool_rating_for_rater.docx` and send only that document. It holds the instructions, the questions of `CARD.md`, the cases of `CASES.md`, blank answer tables and a background section. Do not send the paper, the ledger, this README or the authors' answers.

## For the rater

Everything needed is in the document.

## After it comes back

1. `python v2/validation_kit/docx_to_csv.py RETURNED.docx OUTDIR` writes `answers_rater.csv` and `rater_background.txt`. It reports any answer that is not one of the allowed codes and changes nothing else.
2. `python v2/validation_kit/score_agreement.py answers_authors.csv answers_rater.csv` prints per-item agreement, overall agreement and Cohen's kappa over the items answered by both, and lists the disagreements.
3. Add the authors' file and both rater files to the repository, check that the authors' file still has the recorded hash, and report the numbers whatever they are. With one rater and 15 answers, the paper may say that a second person applied the standard and how often they agreed with the authors. It may not say the standard is validated.

## Data handling

No patient data is involved. The diagnostics are public libraries, read through their own documentation and code.
