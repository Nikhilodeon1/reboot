# Pre-registration, v2, addendum 14: E21 runtime changed to the benchmark's own version pins

Written before the E21 script was run: no output from it had been received.

## Change

Addendum 12 said that the benchmark's old version pins do not install on a current runtime, and that the script would install, unpinned, only the packages that the module-level imports need. That was written for the runtime's default Python. The benchmark's `environment.yml` specifies Python 3.8, and an isolated Python 3.8 interpreter can be created inside the same Colab runtime with the `uv` tool. The script now does that and installs the versions that the benchmark's `requirements.txt` pins at the commit used: numpy 1.23.5, scikit-learn 1.1.3, scipy 1.9.3, ray 2.2.0, torch 1.13.0 (the CPU build), datasets 2.11.0, fairlearn 0.8.0, frozendict 2.3.4, requests 2.28.1, pyarrow 11.0.0, huggingface-hub 0.13.3, dill 0.3.6, fsspec 2022.11.0, joblib 1.2.0 and threadpoolctl 3.1.0. `requirements.txt` gives no version for pandas, folktables or xport. For pandas we pin 1.5.3, a release of the same period. For folktables, xport and every indirect dependency, the installer is limited to releases dated before 1 June 2023.

Only the packages that the module-level imports reach are installed, not the whole requirements file.

## Why

The model and the preprocessing are then run with the library versions that the benchmark names, which removes version differences as an explanation for any difference from E19.

## Unchanged

Everything else in addendum 12: the override of the download step only, the alignment checks, the gate, the reported quantities, the bounds and the rule for a failed run. If the pinned environment cannot be built or the benchmark code does not run in it, we record every change made, and no change to preprocessing, splitting or the model is allowed under the claim that the benchmark's own pipeline was run.
