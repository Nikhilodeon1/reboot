# Pre-registration, v2, addendum 10: E18 (verdict rules at the audit size, and prevalence)

Written before the script ran. It uses the per-stay labels of the 45 operationalization pairs of E8 (addendum 4), read from the local cache. Nothing in the detectors changes.

## Question

At a 500-stay audit, how often does the shipped point rule (flag when the audit kappa is below 0.60) disagree with the whole-cohort verdict, and how do two rules that can say "inconclusive" compare with it? Separately, how much of the difference in kappa between databases could be prevalence?

## Setup

For each of the 45 pairs of labelings on each of the two databases (90 pair and database combinations), the whole-cohort kappa $\theta^\ast$ is computed on all stays, and the truth is the whole-cohort verdict: flag if $\theta^\ast<0.60$, clear otherwise. We draw 2,000 audits of 500 stays without replacement, with numpy seed 20261127 for MIMIC-IV and 20261128 for eICU-CRD, and score every pair on the same audits.

Rules applied to an audit with kappa $\hat\kappa$, observed agreement $p_o$, chance agreement $p_e$ and $n=500$:

- Point rule (shipped): flag if $\hat\kappa<0.60$, otherwise clear.
- Interval rule: the standard error is $\mathrm{se}=\sqrt{p_o(1-p_o)/(n(1-p_e)^2)}$. Flag if $\hat\kappa+1.96\,\mathrm{se}<0.60$, clear if $\hat\kappa-1.96\,\mathrm{se}>0.60$, and inconclusive otherwise. The formula is an approximation, so we check its coverage against a bootstrap on a random sample of 100 audits of the primary control with 400 resamples each.
- Zone rule: inconclusive if the audit's bootstrap flag probability (400 resamples of the audit) lies between 0.05 and 0.95, otherwise flag or clear by the majority. It is computed on 200 audits of the primary control and of five other pairs fixed here: the pairs with the five smallest margins $m$ after the primary control.

## Reported

For each rule and for the combinations grouped by the margin $m=|\tau-\theta^\ast|/\sigma_{500}$ of the whole-cohort value (at most 1.64, 1.64 to 3, above 3): the share of audits whose verdict matches the truth, the share that is inconclusive (interval and zone rules), and the share that is decisive and wrong. For the primary control (MIMIC-IV, single-point against window [-48,+24]): the same three shares, and the audit size at which the interval rule becomes decisive in half of the audits, found by simulation over sizes 500 to the whole cohort.

Prevalence: for the primary control and the two databases, the proportion of positive labels under each labeling, the observed agreement, Cohen's kappa and the prevalence-adjusted and bias-adjusted kappa $2p_o-1$.

## Pre-stated reading

The interval rule is useful if its decisive-wrong share is at most 0.05 in every margin group and its inconclusive share is concentrated at margins at most 1.64. We report the result whether or not this holds. No direction is predicted for the point rule.

## Not done in this addendum

A bootstrap that resamples patients and not stays needs the patient identifiers of the full cohorts. They are not on the machine that runs this script, so the intervals in the paper that resample stays stay as they are, and the paper states that.

## Data handling

Per-stay labels stay outside the repository. The results file holds aggregates only.
