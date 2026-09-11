# Taxonomy of diagnostic failure modes

Four ways a diagnostic — a detector built to audit an ML pipeline for a specific
confound — can fail, independent of whether the confound it targets is real.

Every instance below is checked against this repository. Where a claim could not
be verified it was corrected rather than committed; the corrections are recorded
at the bottom, because a taxonomy that asserts unverified instances would be the
same failure it catalogues.

## Type 1 — Vacuous pass

A check that never reached a verdict is scored as a verdict of "clean". The
absence of a detection is recorded as a detection of absence.

Two sub-forms, which share a consequence and differ in mechanism:

**1a. Falsy-as-clean.** An undecidable or absent result — `nan`, `None`, an
empty container — is consumed by a boolean test, where it is indistinguishable
from "no confound found".

**1b. Degenerate control.** The control itself cannot fail. It passes for
arithmetic or ceiling reasons rather than because the detector discriminated,
and the resulting TN is counted as evidence of specificity.

Instances in this project, four independent occurrences across five pieces of
code (`README.md`, "Finding: diagnostics need an explicit UNDECIDABLE state"):

    1b  check 1's negative control passed the same audit array as both arguments
        to Cohen's kappa. Result 1.0 by construction; TN=2 measured arithmetic.
    1b  detector 1's suspicion-window controls sit at kappa 0.93-1.00. Reported
        bare, TN=3 implies three tests when only one discriminates.
    1a  detector 3's INDETERMINATE on third-party repositories. Folded into TN it
        would have produced TN=3 from files the detector never analysed.
    1a  Task 5's train_test_gap: an undefined in-domain AUROC made
        `nan > threshold` evaluate False, and the abstention scored as correct
        silence — handing the baseline a perfect TP=3 FP=0 FN=0 TN=1 that would
        have contradicted this paper's own headline comparison.

External instance, sub-form 1a: DomainBed's model-selection code, where
`lib/query.py` guards `nan` inside `sorted()` and offers `filter_not_nan`, but
`argmax()` — used by three of four selection methods — is a bare `max()`.
`LeaveOneOutSelectionMethod` additionally guards missing environments with
`any([v == -1 for v in val_accs])`, which is vacuously False on an empty list.
Structurally present, not reachable with shipped datasets; see
`detectors/external/CROSSDOMAIN_UNDECIDABLE.md` and do not overstate it.

The external case is the strongest evidence for this type precisely because the
hazard was known in that file and still slipped one call site.

## Type 2 — Structural non-discriminability

The diagnostic's decision boundary coincides with, or sits arbitrarily close to,
the true value it must separate from. No amount of data resolves this, because it
is not a sampling problem.

Instance: detector 1's MIMIC window-vs-single-point control. `KAPPA_FLAG = 0.60`
(`detectors/checks/check1_label_shift.py:35`), and the full-cohort kappa is
**0.602**, CI [0.597, 0.607] at n=74,829. At the detector's operating point —
repeated 500-patient audit draws — it flags **48.4%** of the time. A coin flip.

The demo-scale value was 0.651 with P(flag) = 0.216. Going to 640x the cohort
moved it TOWARD the threshold, not away. This is the case that proves the type is
real: the hypothesis "small-sample artifact" was tested at full scale and
rejected.

## Type 3 — Granularity / pairing mismatch

The diagnostic is blind to a confound whose structure does not match the
diagnostic's aggregation level or pairing structure.

Instances, both initial false negatives in this project's own detectors
(`README.md`, "Notes that matter"):

    check 5   wrong aggregation granularity
    check 2   unpaired where the comparison is paired

Detector 2's fix is why it is reported as a paired t rather than mean +/- sd: its
unpaired null spread is comparable in size to the effect it must reveal, so the
unpaired form could not see its own signal.

Full scale sharpened this rather than merely repeating it. Detector 5's
composition gate binds nowhere at realistic n — every `gap_ratio` clears the
threshold — so the conjunction collapses into availability-only and one of the
two gates is decorative (`detectors/PREREGISTRATION_OUTCOME.md`). A gate that
does no work is invisible until the diagnostic is examined at the scale it will
actually be used at.

## Type 4 — Post-hoc fitting risk

Redesigning a diagnostic after observing its failure is contaminated evidence,
even when the redesign is well reasoned. Only decision rules fixed in advance
escape this.

Instances (`detectors/PREREGISTRATION.md`, `detectors/PREREGISTRATION_OUTCOME.md`;
the pre-registration was committed at `63f5d95`, before the code that produced
the numbers it governs):

    Variant B rejected under the rule as written, despite higher recall
    (0.73 vs 0.60 at demo scale), because the pre-registered criterion was a
    strictly lower detection floor and B did not deliver one. At full scale the
    two variants are identical on every scored case.

    E3 excluded from scoring in advance, because its ground truth is unknown. It
    is also the ONLY case where the two variants diverge — which is exactly why
    excluding it beforehand mattered.

## Corrections made to the proposed text

Recorded rather than applied silently.

1. **Type 1's definition was widened.** As proposed it covered only falsy values
   (`nan`, `None`, empty). Two of this project's four instances — the tautological
   kappa control and the near-ceiling window controls — are not falsy-value bugs
   at all; they are controls that cannot fail. Under the narrow definition the
   instance count is two, not four. The definition now has two sub-forms so the
   count of four is accurate.

2. **Type 1's instance list had a probable double-count and an omission.** The
   proposed list read "rates(), INDETERMINATE-as-TN, nan-as-silence in the
   baseline checks, the near-ceiling-control pattern's early form". `rates()` and
   "nan-as-silence in the baseline checks" are the same incident, and the
   tautological check 1 control was missing. Replaced with the four occurrences
   as recorded in the README.

3. **Type 3's instances were attributed to the wrong detectors.** The proposed
   text said "detectors 3/4's false-negative fixes". Detectors 3 and 4 are
   deterministic static analysis and had no such fixes. The two granularity /
   pairing false negatives were **check 5** and **check 2**.

Type 2 needed no correction: `KAPPA_FLAG = 0.60` against a true kappa of 0.602 is
exact as proposed.
