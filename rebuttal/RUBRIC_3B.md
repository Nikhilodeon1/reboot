# Task 3b labelling rubric (committed before any site is read)

Extends PREREG_R1.md section 3b. The preregistration names three outcome labels;
a sampled site can also be a pattern match that is not a model-selection
decision, or a sound selection. Those two cases are declared here, before
labelling, so no site is forced into a label that misdescribes it.

## Per site, record

- SELECTION_SPLIT and REPORTED_SPLIT, each from: train, source validation,
  held-out target, OOD target, test, unknown.
- Evidence: file, line range, pinned SHA, and the one or two lines that fix each
  split.
- One outcome label.

## Outcome labels

| Label | Rule |
|---|---|
| CONTAMINATED | The same held-out, OOD or test split drives the selection AND is the split of the number presented as held-out or zero-shot. |
| DISCLOSED_ORACLE | As CONTAMINATED, and the authors state in code or documentation that this is oracle selection. Contaminated by construction; counted separately and never merged into the sensitivity numerator without saying so. |
| AMBIGUOUS | The two splits cannot be established from the file and the configuration it ships with (config-dependent, argument-dependent, or the data is built elsewhere). Counted separately, never folded into either side. |
| SOUND | Selection uses train or source validation, and the reported number uses a different split. |
| NOT_SELECTION | The pattern matched but no model, hyperparameter or checkpoint is being chosen (a statistics helper, a data-processing max, a plotting call). |

## Rules

1. Decide from the file and the configuration it ships with. Do not infer from
   the repository's reputation or its paper.
2. If a decision needs another file, read that file and cite it; if it still
   cannot be fixed, the label is AMBIGUOUS.
3. Labels are assigned BEFORE detector 3 is run on any sampled file, and without
   looking at its output.
4. The sensitivity denominator is k = CONTAMINATED (DISCLOSED_ORACLE reported
   alongside, clearly separated). SOUND and NOT_SELECTION sites carry no
   specificity claim for the detector unless it issues clean verdicts on them.
