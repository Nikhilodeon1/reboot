"""Task 4f (Tier 3): what two verbatim DomainBed lines do on degenerate input.

Copies two short, pure fragments of DomainBed at commit
b93c22a1cfc3b2428398272c1a116c8de1f4139e, exactly as written:

  domainbed/lib/query.py:144      return max(self._list, key=selector)
  domainbed/model_selection.py:153-155
      if any([v==-1 for v in val_accs]):
          return None
      val_acc = np.sum(val_accs) / (n_envs-1)

Inspection: both are pure (no I/O, no mutation outside local names). No repository
import, no I/O, no network; synthetic inputs only.

THIS DEMONSTRATES THE SEMANTICS OF THE VERBATIM PATTERN. IT IS NOT A BUG REPORT
AGAINST SHIPPED DOMAINBED: whether the callers can ever produce these inputs was
not traced.
"""
import numpy as np

nan = float("nan")


def argmax_fragment(records, selector):
    # query.py:144, with `self._list` replaced by `records` and `selector` passed in
    return max(records, key=selector)


def guard_fragment(val_accs, n_envs):
    # model_selection.py:153-155, kept as written; `return val_acc` is added so the value can be printed
    if any([v == -1 for v in val_accs]):
        return None
    val_acc = np.sum(val_accs) / (n_envs - 1)
    return val_acc


sel = lambda r: r["val_acc"]
print("== argmax: max(records, key=selector), five records, NaN position varies")
good = [{"id": i, "val_acc": a} for i, a in enumerate([0.61, 0.70, 0.66, 0.58])]
for pos in (0, 2, 4):
    recs = list(good)
    recs.insert(pos, {"id": "NaN", "val_acc": nan})
    print(f"  NaN record at position {pos}: selected id = {argmax_fragment(recs, sel)['id']}")
print("  empty list:", end=" ")
try:
    argmax_fragment([], sel)
except ValueError as e:
    print("raises ValueError:", e)

print("\n== guard: any([v==-1 ...]) then np.sum(val_accs)/(n_envs-1)")
cases = {
    "all valid [0.6, 0.7]":        ([0.6, 0.7], 3),
    "missing sentinel [0.6, -1]":  ([0.6, -1], 3),
    "NaN value [0.6, nan]":        ([0.6, nan], 3),
    "empty list []":               ([], 1),
    "zero accuracy [0.0, 0.0]":    ([0.0, 0.0], 3),
}
import warnings
warnings.simplefilter("ignore")
for name, (v, n) in cases.items():
    print(f"  {name:<28} -> {guard_fragment(v, n)!r}")

print("\n== composed: a NaN val_acc that passed the guard, then fed to the argmax fragment")
recs = [{"id": "env-with-NaN", "val_acc": guard_fragment([0.6, nan], 3)},
        {"id": "env-b", "val_acc": guard_fragment([0.7, 0.8], 3)}]
print("  selected id =", argmax_fragment(recs, sel)["id"], "(NaN listed first)")
recs.reverse()
print("  selected id =", argmax_fragment(recs, sel)["id"], "(NaN listed second)")
