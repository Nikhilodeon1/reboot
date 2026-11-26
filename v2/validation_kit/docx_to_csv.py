"""Read the returned rater document and write answers_rater.csv and rater_background.txt (standard library only).

    python v2/validation_kit/docx_to_csv.py RETURNED.docx OUTDIR

The text of each box is copied as typed. Answer codes are lower-cased and stripped; anything that is not one of the allowed codes is
reported and left as typed, so that nothing is silently corrected.
"""
import os
import re
import sys
import csv
import zipfile
import xml.etree.ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
ALLOWED = {"yes", "no", "partly", "unclear", "control_only", "convention_only"}


def cell_text(tc):
    paras = []
    for p in tc.iter(W + "p"):
        paras.append("".join((t.text or "") if t.tag == W + "t" else " " for t in p.iter() if t.tag in (W + "t", W + "tab", W + "br")))
    return " ".join(x.strip() for x in paras if x.strip())


def main(path, outdir):
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    answers, background = [], []
    for tbl in root.iter(W + "tbl"):
        rows = [[cell_text(tc) for tc in tr.findall(W + "tc")] for tr in tbl.findall(W + "tr")]
        if not rows:
            continue
        if rows[0][:1] == ["Row ID"]:
            for r in rows[1:]:
                m = re.match(r"^\s*(\d)\s*\|\s*(\S+)", r[0])
                if m:
                    answers.append({"case": m.group(1), "item": m.group(2), "answer": r[2].strip().lower().rstrip("."), "evidence": r[3]})
        elif rows[0][:1] == ["Question"]:
            background += [f"{r[0]}: {r[1]}" for r in rows[1:]]
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "answers_rater.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["case", "item", "answer", "evidence"])
        w.writeheader()
        w.writerows(answers)
    with open(os.path.join(outdir, "rater_background.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(background) + "\n")
    print(f"{len(answers)} answer rows, {len(background)} background rows")
    for a in answers:
        if a["answer"] not in ALLOWED:
            print(f"check by hand: case {a['case']} {a['item']}: answer {a['answer']!r}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
