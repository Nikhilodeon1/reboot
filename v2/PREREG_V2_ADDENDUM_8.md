# Pre-registration, v2, addendum 8: E16 execution on a second machine

Written before seeds 48 to 61 ran. Seeds 42 to 47 are unchanged.

## Change

Addendum 7 registered E16 with seeds 47 to 61. Seed 47 ran on the authors' desktop CPU as the timing pilot. Seeds 48 to 61 run on Google Colab CPU runtimes, in lanes of one process with 2 threads each, with the same script (`v2/scripts/e9_full_scale.py`, tasks `dose,arms,base`), the same arrays and the same protocol (small model, 3 epochs, CPU). No GPU runtime is used, because a GPU would change the arithmetic of the registered protocol. The script gains one field per result file, `cpu`, that records the processor model and the Python version. It does not change any computation.

## Why this matters for the readings

The full-scale tier already showed that a rerun on a second CPU shifts t by up to about 0.5 with the same flags (Section 7 of the paper). Seeds 42 to 47 come from the desktop and seeds 48 to 61 from Colab, so the 20-seed values mix two processors, and the processors in Colab can differ between sessions. Several readings sit within 0.5 of their critical values.

## Hardware check

Before the analysis, the no-leak arm A0 at seed 42 is retrained on Colab and compared with the stored desktop loss (0.0053399530142078724). We report the relative difference. A0 enters every reduction r, so this difference bounds the shift that the hardware alone can add to each seed.

## Reported

Everything in addendum 7, plus the hardware check, plus the `cpu` field of every result file in a table of counts per processor model. If a verdict at 2%, 5% or 20% differs between the 20-seed analysis and the same analysis restricted to the seeds of one processor model that has at least five seeds, we report both. No seed is dropped, and a failed task is rerun on the same kind of runtime.

## Pre-stated predictions

None about direction, as in addendum 7.

## Data handling

Unchanged. The arrays are patient-level derivatives of credentialed data. They go to the authors' private Google Drive only, never to the repository, and only aggregate losses are written to results.
