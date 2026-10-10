"""QA gates for the revised manuscript and the response drafts.

    python rebuttal/scripts/qa_check.py [--paper DIR]

1 ledger check: every number in the revised text and the responses must occur in the ledger,
  the submitted manuscript or numbers.json (rounding allowed); exceptions are printed.
2 anonymity scan, 3 banned phrases, 4 build facts (pages, overfull boxes, undefined references),
5 citations: new references must be named in CITATIONS_VERIFIED.md.
Exit status 1 if gates 2, 3 or 5 fail or the build is not clean; gate 1 lists exceptions for review.
"""
import os
import re
import sys
import json
import argparse

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REB = os.path.join(ROOT, "rebuttal")
DEFAULT_PAPER = os.path.join(os.path.dirname(ROOT), "ml4h_PAPERS", "RebootPCL Paper")

NUM = re.compile(r"(?<![A-Za-z0-9\\_/.])[-+]?\d+(?:\.\d+)?(?![A-Za-z0-9])")
ANON = [r"C:[\\/]+Users", r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}",
        r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b"]
NAMES_FILE = os.environ.get("QA_NAMES_FILE", os.path.join(os.path.dirname(os.path.dirname(ROOT)), "work_reboot", "anon_names.txt"))
if os.path.exists(NAMES_FILE):   # identifying strings live outside the repository
    ANON += [re.escape(x.strip()) for x in open(NAMES_FILE, encoding="utf-8") if x.strip()]
BANNED = ["validated", "FPR 0", "FPR $0", "worse with data", "order of magnitude", "expected direction",
          "renders a verdict", "\u2014"]


def read(p):
    return open(p, encoding="utf-8", errors="replace").read()


def strip_tex(s):
    s = s.replace("{,}", "")
    s = re.sub(r"(?m)^%.*$", "", s)
    s = re.sub(r"\\(?:label|ref|cite[a-z]*|citet|citep|sectionref|tableref|appendixref|includegraphics|url)\{[^}]*\}", " ", s)
    s = re.sub(r"\\(?:begin|end)\{[^}]*\}", " ", s)
    s = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?", " ", s)
    return s


def tokens(text):
    text = re.sub(r"(?:Section|Sections|Table|Appendix|App)\s+\S+", " ", text)
    out = set()
    for m in NUM.findall(text):
        t = m.lstrip("+")
        if t in ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"):
            continue
        if len(t.lstrip("-")) >= 7 and "." not in t:   # commit hash made only of digits
            continue
        out.add(t)
    return out


def in_corpus(tok, corpus):
    c = tok.lstrip("-")
    if c in corpus:
        return True
    if "." in c:
        dec = len(c.split(".")[1])
        for m in NUM.findall(corpus):
            m = m.lstrip("+-")
            if "." in m and abs(round(float(m), dec) - float(c)) < 1e-12:
                return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paper", default=DEFAULT_PAPER)
    a = ap.parse_args()
    fail = False
    rev = read(os.path.join(a.paper, "main.tex"))
    orig = read(os.path.join(REB, "manuscript", "main_original.tex"))
    ledger = read(os.path.join(REB, "LEDGER.md"))
    nums = read(os.path.join(REB, "numbers.json"))
    corpus = ledger + "\n" + orig + "\n" + nums
    responses = {f: read(os.path.join(REB, f)) for f in sorted(os.listdir(REB)) if f.startswith("RESPONSE_") and f.endswith(".md")}

    print("== 1 ledger check")
    exc = {}
    for name, text in [("main.tex", strip_tex(rev))] + list(responses.items()):
        bad = sorted(t for t in tokens(text) if not in_corpus(t, corpus))
        exc[name] = bad
        print(f"{name}: {len(bad)} numbers not in ledger / original / numbers.json:", ", ".join(bad[:60]))

    print("\n== 2 anonymity scan")
    files = [os.path.join(a.paper, "main.tex"), os.path.join(a.paper, "ref.bib")]
    for dp, dn, fn in os.walk(REB):
        dn[:] = [d for d in dn if d not in ("__pycache__",)]
        for f in fn:
            if f.endswith((".md", ".json", ".csv", ".txt", ".py", ".tex", ".bib", ".sh")):
                files.append(os.path.join(dp, f))
    hits = 0
    for f in files:
        t = read(f)
        for pat in ANON:
            for m in re.finditer(pat, t, re.I):
                s = m.group(0)
                if re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-.*", s) and f.endswith(".json"):
                    continue
                if "anonymous" in s.lower() or s.lower().endswith("example.invalid") or "4open.science" in s:
                    continue
                hits += 1
                print(f"  HIT {os.path.relpath(f, ROOT)}: {s!r}")
    print(f"anonymity hits: {hits}")
    fail |= hits > 0

    print("\n== 3 banned phrases")
    nb = 0
    for name, text in [("main.tex", rev)] + list(responses.items()):
        for b in BANNED:
            if b.lower() in text.lower():
                nb += 1
                print(f"  {name}: {b!r}")
    print(f"banned-phrase hits: {nb}")
    fail |= nb > 0

    print("\n== 4 build facts")
    log = read(os.path.join(a.paper, "main.log"))
    over = len(re.findall(r"Overfull", log))
    undef = len(re.findall(r"(?:Citation|Reference)[^\n]*undefined", log))
    pages = re.search(r"Output written on main\.pdf \((\d+) pages", log)
    print(f"overfull boxes: {over}; undefined refs/citations: {undef}; total pages: {pages.group(1) if pages else '?'}")
    try:
        import pypdf
        r = pypdf.PdfReader(os.path.join(a.paper, "main.pdf"))
        for i, p in enumerate(r.pages, 1):
            t = p.extract_text() or ""
            if "Conclusion" in t and "References" in t:
                lines = [ln for ln in t.splitlines() if ln.strip()]
                print(f"main text ends on page {i}, which also holds the references; "
                      f"page limit is 8 excluding references, so at least {8 - i} full page(s) spare")
    except Exception as e:
        print("pdf check skipped:", e)
    fail |= over > 0 or undef > 0

    print("\n== 5 citations")
    cv = read(os.path.join(REB, "CITATIONS_VERIFIED.md"))
    bib_new = [("yang2022leakage", "Yang"), ("subotic2022leakage", "Suboti")]
    for key, sur in bib_new:
        ok = sur in cv and key in read(os.path.join(a.paper, "ref.bib"))
        print(f"  {key}: {'verified entry present' if ok else 'MISSING'}")
        fail |= not ok

    print("\nQA", "FAILED" if fail else "passed (gate 1 exceptions listed above need review)")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
