#!/usr/bin/env bash
# E16 lane: runs the 11 tasks per seed for the seeds given as arguments, one seed after another.
# Resumable: finished (seed, task) files are skipped, so a killed lane can simply be started again.
# Usage:  ARR=/path/to/arrays OUT=/path/to/results REPO=/path/to/repo bash v2/scripts/e16_lane.sh 48 49 ...
# Arrays hold patient-level derivatives of credentialed data: keep them outside the repository.
set -u
: "${ARR:?set ARR to the arrays directory}"
: "${OUT:?set OUT to the results directory}"
: "${REPO:?set REPO to the repository root}"
THREADS="${THREADS:-2}"
mkdir -p "$OUT"
cd "$REPO" || exit 1
for S in "$@"; do
  echo "=== seed $S start $(date -u +%FT%TZ)"
  PCL_TEST_MODE=1 python -W ignore v2/scripts/e9_full_scale.py run \
    --arrays "$ARR" --seed "$S" --tasks dose,arms,base --only A0,A1@2,A2@2,A1@5,A2@5,A1@20,A2@20,A3@5,A4@5,A3@20,A4@20 --out "$OUT" --threads "$THREADS"
  echo "=== seed $S end $(date -u +%FT%TZ)"
done
