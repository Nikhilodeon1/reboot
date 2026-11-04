"""Sentence-length statistics for the paper's running prose (tables, figures and math removed).

    python v2/scripts/prose_stats.py [N]

Prints mean and median sentence length, the number of sentences over 35 words, and the N longest sentences, so the edit pass
can split them (target from the voice skill: average 15 to 25 words, a short sentence after any dense one).
"""
import os
import re
import sys
import statistics

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(os.path.dirname(HERE), "paper", "main.tex")


def prose(t):
    body = t.split(r"\begin{document}")[1].split(r"\bibliographystyle")[0]
    body = re.sub(r"(?m)%.*$", "", body)
    for env in ("table", "figure", "tikzpicture", "tabular", "definition"):
        body = re.sub(r"\\begin\{" + env + r"\*?\}.*?\\end\{" + env + r"\*?\}", "", body, flags=re.S)
    body = re.sub(r"\\(?:cite[pt]?|ref|label|pending)\*?(?:\[[^\]]*\])?\{[^}]*\}", " ", body)
    body = re.sub(r"\\(?:item|paragraph|section|subsection)\*?(?:\{[^}]*\})?", " ", body)
    body = re.sub(r"\$[^$]*\$", "X", body)
    body = re.sub(r"\\[a-zA-Z]+\*?", " ", body)
    return re.sub(r"[{}~]", " ", body)


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    text = prose(open(TEX, encoding="utf-8").read())
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.split()) > 3]
    L = [len(s.split()) for s in sents]
    print(len(L), "sentences; mean", round(statistics.mean(L), 1), "median", statistics.median(L),
          "; over 35 words:", sum(l > 35 for l in L), "; 12 words or fewer:", sum(l <= 12 for l in L))
    for s in sorted(sents, key=lambda s: -len(s.split()))[:n]:
        print(len(s.split()), "|", " ".join(s.split())[:200])


if __name__ == "__main__":
    main()
