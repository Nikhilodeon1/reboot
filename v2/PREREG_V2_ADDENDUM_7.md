# Pre-registration, v2, addendum 7: E16 (more seeds for the near-threshold detector 2 readings)

Written before any new seed ran.

## E16. Fifteen more seeds for the readings that sit near their thresholds

**Question.** Do the near-threshold full-scale readings of detector 2 (the shipped statistic at the 2% dose, t = 1.94 against 2.132, and the mask-transplant comparison at 5% and 20%, t = 2.58 and 2.11) keep their verdicts with 20 seeds instead of five?

**Design.** Seeds 47 to 61 are added to seeds 42 to 46. Same protocol, split, pool and probe indices as the full-scale tier (small model, 3 epochs, CPU, 2 threads per process). Per new seed, 11 tasks: the no-leak arm A0; A1 and A2 at 2%, 5% and 20% of the pool; A3 and A4 at 5% and 20%. Seed 47 runs first as a timing pilot and is part of the set. Seeds 42 to 46 keep their stored runs, so the 5% and 20% values for those seeds are the ones already reported.
Before any new seed, the script retrains the no-leak arm A0 for seed 42 and compares it with the stored loss, as it did for A2 at 5%.

**Reported.** For the 2% dose, the 5% and 20% arms and the missingness share R, the 20-seed values of r1, r2, r3, r4, t for the shipped statistic, the paired t for A3 against A2 and R, next to the five-seed values. The critical value is the one-sided 5% value for the number of seeds (2.132 at 5 seeds, 1.729 at 20). The reading rules of addendum 4 apply unchanged. No seed is dropped, and a failed task is rerun, not skipped.

**Pre-stated predictions.** None about direction. We report any verdict that flips, in either direction, as a result.

**Data handling.** Only aggregate losses leave the arrays, which stay outside the repository.
