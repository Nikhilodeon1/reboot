# Diagnostics to rate (versions pinned on 2026-11-26)

Use the versions below. Record the URLs you read. If a documentation page describes a newer version, say so in the evidence.

1. Great Expectations 1.25.0 (source: github.com/fivetran/great_expectations, tag 1.25.0): the column expectation `expect_column_mean_to_be_between` with the pandas execution engine, which returns a success flag.
2. Deepchecks 0.19.1 (source: github.com/deepchecks/deepchecks, tag 0.19.1): the tabular train-test check on feature drift, `FeatureDrift` (older name `TrainTestFeatureDrift`), with its default condition `add_condition_drift_score_less_than`.
3. Evidently 0.7.23 (source: github.com/evidentlyai/evidently, tag v0.7.23): the data drift check for one column (the `ValueDrift` metric, also used by `DataDriftPreset`), with its default statistical test and threshold.
