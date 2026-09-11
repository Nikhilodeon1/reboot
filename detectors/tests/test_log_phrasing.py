"""Committed logs must not carry retracted wording or verdicts.

Scans logs/*.out only; prose docs discuss the retraction legitimately.
"""
import glob
import io
import os
import unittest

LOGS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "logs")

# (glob, phrase, reason). "DETECTOR VALIDATED" scoped to check5: checks 1-2
# print it legitimately.
BANNED = [
    ("*.out", "share of gap explained",
     "composition_gap_ratio is not a share and can exceed 1.0 (E4 = 1.414); "
     "this wording was retracted"),
    ("*.out", "share of the gap explained",
     "same retraction, alternate wording"),
    ("check5*.out", "DETECTOR VALIDATED",
     "detector 5's positive case is a documented FALSE NEGATIVE; a check5 log "
     "claiming validation predates the sampling fix"),
]


class TestLogPhrasing(unittest.TestCase):
    def test_no_retracted_phrasing_in_logs(self):
        self.assertTrue(sorted(glob.glob(os.path.join(LOGS, "*.out"))),
                        "no logs found -- the guard would pass vacuously")
        offenders = []
        for pattern, phrase, why in BANNED:
            files = sorted(glob.glob(os.path.join(LOGS, pattern)))
            self.assertTrue(files, f"no log matches {pattern!r}: this rule "
                                   "would pass vacuously")
            for path in files:
                text = io.open(path, encoding="utf-8", errors="replace").read()
                if phrase in text:
                    offenders.append(f"{os.path.basename(path)}: "
                                     f"{phrase!r} — {why}")
        self.assertEqual(offenders, [],
                         "stale committed logs:\n  " + "\n  ".join(offenders))


if __name__ == "__main__":
    unittest.main()
