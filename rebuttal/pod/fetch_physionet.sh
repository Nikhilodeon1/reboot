#!/usr/bin/env bash
# Download only the MIMIC-IV v3.1 and eICU-CRD v2.0 files the loaders read, into
# POD_SCRATCH/data. Needs your own credentialed PhysioNet account; the username and
# password are typed at the prompt and kept only in this shell's memory. Resumable
# (wget -c): rerun the same command if it is interrupted.
#
#   bash rebuttal/pod/fetch_physionet.sh
#
# The data-use agreement allows holding the data here only while you work on it:
# delete $POD_SCRATCH/data when the runs are finished.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$here/env.sh"

read -r -p "PhysioNet username: " PN_USER
read -r -s -p "PhysioNet password: " PN_PASS
echo

MIMIC="hosp/patients hosp/admissions hosp/labevents hosp/diagnoses_icd hosp/microbiologyevents hosp/prescriptions icu/icustays icu/chartevents icu/inputevents icu/outputevents"
EICU="patient diagnosis lab vitalPeriodic vitalAperiodic nurseCharting medication infusionDrug intakeOutput microLab"

cd "$POD_SCRATCH/data"
for f in $MIMIC; do
  wget -c -q --show-progress -x -nH --cut-dirs=1 --user "$PN_USER" --password "$PN_PASS" \
       "https://physionet.org/files/mimiciv/3.1/$f.csv.gz"
done
for f in $EICU; do
  wget -c -q --show-progress -x -nH --cut-dirs=1 --user "$PN_USER" --password "$PN_PASS" \
       "https://physionet.org/files/eicu-crd/2.0/$f.csv.gz"
done
unset PN_PASS
echo "MIMIC_DIR=$POD_SCRATCH/data/mimiciv/3.1"
echo "EICU_DIR=$POD_SCRATCH/data/eicu-crd/2.0"
du -sh "$POD_SCRATCH/data/mimiciv" "$POD_SCRATCH/data/eicu-crd"
