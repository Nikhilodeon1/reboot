"""E18b (exploratory): a re-tabulation of the E18 results by margin group, as shares of all audits. No new sampling.

    python v2/scripts/e18b_rule_baselines.py   ->  v2/results/e18b_rule_baselines.json

Added to the repository after the table was first computed; it reads only e18_verdict_rules.json.
"""
import json
import os

import numpy as np

V2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def summarise(rows):
    point = float(np.mean([r["point_match"] for r in rows]))
    match = float(np.mean([r["interval_match"] for r in rows]))
    against = float(np.mean([r["interval_wrong"] for r in rows]))
    return {"combos": len(rows), "point_match": point, "point_against": 1.0 - point, "interval_match": match,
            "interval_against": against, "interval_inconclusive": float(np.mean([r["interval_inconclusive"] for r in rows])),
            "interval_against_share_of_decisive": against / (match + against) if match + against else 0.0}


def main():
    d = json.load(open(os.path.join(V2, "results", "e18_verdict_rules.json")))
    combos = d["combos"]
    out = {"m>3": summarise([c for c in combos if c["margin"] > 3]),
           "1.64<m<=3": summarise([c for c in combos if 1.64 < c["margin"] <= 3]),
           "m<=1.64": summarise([c for c in combos if c["margin"] <= 1.64]),
           "primary": summarise(d["primary_row"])}
    json.dump(out, open(os.path.join(V2, "results", "e18b_rule_baselines.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
