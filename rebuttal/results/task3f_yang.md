# Task 3f: Yang et al. leakage-analysis baseline

Executed 2026-10-08, inside Docker, on both detector 3 fixtures
(`detectors/fixtures/sweep_BUGGY.py`, `sweep_FIXED.py`). Third-party code was
built and run only in the container; nothing from it was imported on the host.

## What was run

- Tool: `github.com/malusamayo/leakage-analysis`, commit
  `a7d038bfec6b8ddbe21d87dde54b806aecdd79f7`; its pyright submodule
  `github.com/malusamayo/pyright` at `e3d7d9c44ac69fa6bc66bb8a47377fcec034e503`.
- Command: `docker run --rm -v <scratch dir>:/data <image> /data/<fixture>.py -o`
  on a copy of each fixture, so no output touched the repository.
- Gate: 90 minutes from 02:06 (local); the image was ready at about 02:30.

## The unmodified Dockerfile does not build

`FROM ubuntu:latest` resolves to a release that no longer ships `libffi7`, so
`apt install -y souffle` fails (souffle 2.4 `Depends: libffi7`). The tool was not
runnable as shipped. Verbatim apt output: `Unsatisfied dependencies: souffle :
Depends: libffi-dev but it is not going to be installed`, then `Depends libffi7
(>= 3.3~20180313)`, build exit code 100.

## The variant that built (three changes, each forced by a build failure)

1. Base image `ubuntu:20.04` instead of `ubuntu:latest` (souffle and Python 3.8
   exist there).
2. `npm install --unsafe-perm` instead of `npm install`: as root, npm 6 skipped the
   lifecycle script that installs the package dependencies, so `webpack` was
   missing at the build step.
3. Node 14.21.3 from nodejs.org installed before the pyright steps: apt's Node 10
   lacks `Object.fromEntries`, which the pyright fork's webpack config uses.

## Result: it reports nothing on both fixtures

Summary table in the generated report, identical for the buggy and corrected
fixture:

| Leakage | #Detected Locations |
|---|---|
| Pre-processing leakage | 0 |
| Overlap leakage | 0 |
| No independence test data | 0 |

"No independence test data" is the tool's multi-test-leakage category, the one
adjacent to detector 3.

The zero is not a clean bill of health. The tool's own intermediate relations are
empty on both files: `ModelPair`, `TestDataWithModel`, `TrainingDataWithModel`,
`ValDataWithModel`, `TorchModelWithData`, `ModelPairCandidate`, `OverlapLeak`,
`NoTestData` and `MultiUseTestLeak` all have 0 rows. It recognised no
train/validation/test model pairing in either fixture, so there was nothing for
its leakage rules to fire on. The buggy and corrected fixtures are
indistinguishable to it. I did not establish why the pairing is not recognised
(the fixtures are PyTorch scripts with custom loaders and the tool is described
for notebook-style scikit-learn pipelines), and no claim about the cause is made.

What this supports: the tool, run unmodified apart from environment changes, does
not detect the model-selection contamination in detector 3's fixtures and does not
tell the buggy file from the fixed one. What it does not support: any statement
that the tool is wrong or weak in general, or that it is clean on these files.
