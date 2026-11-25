# Diagnostics to rate

Use the current stable release of each library and record the version and the URLs you read. Each case names one verdict-emitting check.

1. Great Expectations: a column expectation that returns a success flag, for example `expect_column_mean_to_be_between` with the pandas execution engine. Read its documentation page, and its behavior on an empty or all-missing column in the source or the documentation.
2. Deepchecks: a data check with a pass or fail condition on drift between a training table and a test table, for example `TrainTestFeatureDrift` with its default condition. Read the documentation of the check and of the condition, including the default threshold.
3. Evidently: the data drift test or preset that reports whether drift was detected for a column, with its default statistical test and threshold. Read the documentation of the test and of its default.

If one of these cannot be found in the current release, tell the authors and name the closest verdict-emitting check in the same library.
