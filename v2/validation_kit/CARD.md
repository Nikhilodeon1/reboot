# Reporting card for a diagnostic

A diagnostic is a procedure that takes the artifacts of an ML pipeline (a table, a model, a file) and returns a verdict about one confound, such as a pass or fail, a flag, or a drift alert. It has a statistic, a decision rule that maps the statistic to a verdict, and, optionally, controls (known positive and known negative cases) that validate the pair.

For each diagnostic, answer the five items below with the allowed codes. Write the evidence (a URL and a sentence or line) for every answer.

1. Decidability. When the statistic cannot be computed (an empty table, a column of all missing values, a constant column, a single class), does the diagnostic say so, separately from a pass?
   Codes: `yes` (it reports undecidable, abstains, or raises an error), `no` (it returns a pass or a finite value with no warning), `partly` (it depends on the case; name the cases), `unclear`.
2. Control margins. Does the documentation or output give a known-negative control for the diagnostic, and say how far its statistic lies from the threshold in units of the statistic's sampling spread?
   Codes: `yes`, `control_only` (a control is given and no distance), `no`, `unclear`.
3. Uncertainty at the operating point. Does the output or documentation say how likely the verdict is to change if the data were resampled at the sample size used, for example through an interval, a p-value with its reading rule, or a flag probability?
   Codes: `yes`, `partly` (an interval or p-value but no statement about the verdict), `no`, `unclear`.
4. Null rate and nuisance control. Does the documentation report how often the diagnostic flags when there is no effect (a null rate), or a control that holds a nuisance variable fixed (for example sample size)?
   Codes: `yes`, `partly`, `no`, `unclear`.
5. Provenance of the decision rule. Does the documentation say where the default threshold or rule comes from (a derivation, a cited source, a convention) and whether it was set before looking at data?
   Codes: `yes` (a derivation or source is given), `convention_only` (stated as a default or convention), `no`, `unclear`.
