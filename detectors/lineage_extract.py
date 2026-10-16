






import ast
import os






EQUATION_SIGNATURES = {
    "severinghaus": {"constants": {23400.0}, "calls": {"cbrt"},
                     "names_any": set(), "names_all": set()},
    "henderson_hasselbalch": {"constants": {6.1, 0.0307}, "calls": {"log10"},
                              "names_any": set(), "names_all": set()},
    "base_excess_to_hco3": {"constants": {24.0, 0.5}, "calls": set(),
                            "names_any": {"be", "BaseExcess", "base_excess"},
                            "names_all": set()},
    "map_identity": {"constants": {3.0}, "calls": set(),
                     "names_any": set(), "names_all": {"SBP", "DBP"}},
}


def _constants(node):
    return {float(n.value) for n in ast.walk(node)
            if isinstance(n, ast.Constant) and isinstance(n.value, (int, float))
            and not isinstance(n.value, bool)}


def _calls(node):
    out = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Name):
                out.add(f.id)
            elif isinstance(f, ast.Attribute):
                out.add(f.attr)
    return out


def _names(node):
    out = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Name):
            out.add(n.id)
        elif isinstance(n, ast.Constant) and isinstance(n.value, str):
            out.add(n.value)
        elif isinstance(n, ast.Attribute):
            out.add(n.attr)
    return out


def match_equation(node):

    consts, calls, names = _constants(node), _calls(node), _names(node)
    best, best_score = None, -1
    for eq, sig in EQUATION_SIGNATURES.items():
        if not sig["constants"] <= consts:
            continue
        if sig["names_any"] and not sig["names_any"] & names:
            continue
        if not sig["names_all"] <= names:
            continue

        score = len(sig["constants"]) + bool(sig["calls"] & calls)
        if score > best_score:
            best, best_score = eq, score
    return best


def classify_guard(test):







    out = []
    for node in ast.walk(test):
        if not isinstance(node, ast.Compare) or len(node.ops) != 1:
            continue
        op = node.ops[0]
        if not isinstance(op, (ast.In, ast.NotIn)):
            continue
        left = node.left
        if not (isinstance(left, ast.Constant) and isinstance(left.value, str)):
            continue
        target = node.comparators[0]

        if not (isinstance(target, ast.Attribute) and target.attr == "columns"):
            continue
        out.append(("column_absent" if isinstance(op, ast.NotIn)
                    else "column_present", left.value))
    return out or [("unknown", None)]


def _var_for_index(node, index_names):

    for n in ast.walk(node):
        if isinstance(n, ast.Name) and n.id in index_names:
            return index_names[n.id]
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            return n.value
    return None


def extract_lineage(path, variables):




    with open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())


    index_names = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and \
                isinstance(node.targets[0], ast.Name):
            for s in ast.walk(node.value):
                if isinstance(s, ast.Subscript) and isinstance(
                        s.value, ast.Name) and "IDX" in s.value.id.upper():
                    key = s.slice
                    if isinstance(key, ast.Constant) and \
                            isinstance(key.value, str):
                        index_names[node.targets[0].id] = key.value



    found = {}

    def visit(body, guards, taint):
        for stmt in body:
            if isinstance(stmt, ast.If):
                g = guards + classify_guard(stmt.test)
                visit(stmt.body, g, dict(taint))
                visit(stmt.orelse, guards, dict(taint))
                continue
            if isinstance(stmt, (ast.For, ast.While, ast.With)):
                visit(stmt.body, guards, taint)
                continue
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef,
                                 ast.ClassDef)):
                visit(stmt.body, guards, {})
                continue
            if not isinstance(stmt, ast.Assign):
                continue

            eq = match_equation(stmt.value)
            if eq is None:

                for n in ast.walk(stmt.value):
                    if isinstance(n, ast.Name) and n.id in taint:
                        eq = taint[n.id]
                        break
            if eq is None:
                continue

            for tgt in stmt.targets:
                if isinstance(tgt, ast.Name):
                    taint[tgt.id] = eq
                var = _var_for_index(tgt, index_names)
                if var in variables:
                    found[var] = {
                        "kind": "derived", "equation": eq,
                        "sources": sorted((_names(stmt.value) | set(taint))
                                          & set(variables)),
                        "guards": guards, "line": stmt.lineno}

    visit(tree.body, [], {})
    return found


def resolve(lineage, available_columns):




    out = {}
    cols = set(available_columns)
    for var, rec in lineage.items():
        reachable, why = True, []
        for kind, col in rec["guards"]:
            if kind == "column_absent" and col in cols:
                reachable = False
                why.append(f'guarded by "{col}" not in columns, but "{col}" '
                           f'IS present')
            elif kind == "column_present" and col is not None and col not in cols:
                reachable = False
                why.append(f'guarded by "{col}" in columns, but "{col}" is absent')
        out[var] = dict(rec, reachable=reachable, reason="; ".join(why))
    return out


def to_detector4_lineage(resolved, measured_vars):

    table = {v: "measured" for v in measured_vars}
    for var, rec in resolved.items():
        if rec["reachable"]:
            src = rec["sources"][0] if rec["sources"] else "unknown"
            table[var] = ("derived", rec["equation"], src)
    return table
