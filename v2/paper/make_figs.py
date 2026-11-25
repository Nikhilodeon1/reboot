"""Figures for the v2 paper, drawn from archived aggregate results only.

    python v2/paper/make_figs.py

Fig. 2 reads v2/results/e3_d1_audit_size.json (E3). Fig. 3 reads the round-1 results for detector 2 at demonstration
scale and v2/results/e16_summary.json (E16, 20 seeds) at full scale. Nothing here recomputes a statistic; r2/r1 is
the ratio of the arm means in the archived files.
"""
import os
import json
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.dirname(HERE)
R1 = os.path.join(V2, "evidence_r1", "rebuttal", "results")
OUT = os.path.join(HERE, "figs")
os.makedirs(OUT, exist_ok=True)

plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "pdf.fonttype": 42, "figure.dpi": 150})
C = {"mimic": "#1b6ca8", "eicu_pos": "#b5472a", "eicu_ctrl": "#6b6b6b"}


def fig_audit_size():
    d = json.load(open(os.path.join(V2, "results", "e3_d1_audit_size.json")))
    names = [("MIMIC control", "MIMIC-IV control (kappa 0.602)", C["mimic"]),
             ("eICU positive", "eICU-CRD positive (kappa 0.451)", C["eicu_pos"]),
             ("eICU control", "eICU-CRD control (kappa 0.826)", C["eicu_ctrl"])]
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(7.2, 2.9), gridspec_kw={"width_ratios": [1.1, 1]})
    for key, label, col in names:
        rows = d["cases"][key]["rows"]
        n = [r["n"] for r in rows]
        ax.plot(n, [r["p_hat"] for r in rows], "-", color=col, lw=1.2)
        ax.errorbar(n, [r["p_obs"] for r in rows],
                    yerr=[[r["p_obs"] - r["cp95"][0] for r in rows], [r["cp95"][1] - r["p_obs"] for r in rows]],
                    fmt="o", ms=3.5, color=col, capsize=2, lw=0.9, label=label)
        # panel b: signed margin (tau - theta*) / sigma_n, with the model sigma fixed before the run
        z = [(d["threshold"] - d["cases"][key]["theta_star"]) / r["sd_model"] for r in rows]
        bx.errorbar(z, [r["p_obs"] for r in rows],
                    yerr=[[r["p_obs"] - r["cp95"][0] for r in rows], [r["cp95"][1] - r["p_obs"] for r in rows]],
                    fmt="o", ms=3.5, color=col, capsize=2, lw=0.9)
    ax.axhspan(0.05, 0.95, color="#000000", alpha=0.04, lw=0)
    ax.set_xscale("log")
    ax.set_xlabel("audit size n (stays per audit draw)")
    ax.set_ylabel("flag probability, kappa < 0.60")
    ax.set_ylim(-0.03, 1.03)
    ax.legend(frameon=False, fontsize=7, loc="center", bbox_to_anchor=(0.6, 0.74))
    ax.set_title("(a) against audit size", fontsize=9)
    grid = [i / 20.0 for i in range(-120, 181)]
    bx.plot(grid, [0.5 * (1 + math.erf(g / math.sqrt(2))) for g in grid], "-", color="#000000", lw=1.0)
    bx.set_xlim(-6, 9)
    bx.set_xlabel("signed margin in SDs of the audit statistic")
    bx.set_ylim(-0.03, 1.03)
    bx.set_title("(b) against margin; line is Φ(margin)", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig2_audit_size.pdf"))
    plt.close(fig)


def ratio(path, key, level):
    d = json.load(open(path))
    if key == "demo":
        arms = d["levels"][str(level)]["arms"]
    else:
        arms = d["task2"][str(level)]["arms"]
    return arms["A2"]["mean"] / arms["A1"]["mean"]


def fig_volume():
    demo = os.path.join(R1, "task2_demo.json")
    _ri = json.load(open(os.path.join(V2, "results", "ratio_interval.json")))
    _e16 = json.load(open(os.path.join(V2, "results", "e16_summary.json")))["all20"]["dose"]
    FIELLER = {("Demonstration", 5): _ri["demonstration_5pct"]["fieller95"], ("Demonstration", 20): _ri["demonstration_20pct"]["fieller95"],
               ("Full", 5): _e16["5"]["fieller95"], ("Full", 20): _e16["20"]["fieller95"]}
    vals = {("Demonstration", 5): ratio(demo, "demo", 5), ("Demonstration", 20): ratio(demo, "demo", 20),
            ("Full", 5): _e16["5"]["ratio"], ("Full", 20): _e16["20"]["ratio"]}
    fig, ax = plt.subplots(figsize=(3.6, 2.8))
    xs = {("Demonstration", 5): 0, ("Demonstration", 20): 1, ("Full", 5): 2.4, ("Full", 20): 3.4}
    cols = {"Demonstration": "#7f9fbf", "Full": "#1b6ca8"}
    for k, v in vals.items():
        ax.bar(xs[k], v, width=0.8, color=cols[k[0]])
        lo, hi = FIELLER[k]
        ax.errorbar(xs[k], v, yerr=[[v - max(lo, 0.0)], [hi - v]], fmt="none", ecolor="black", capsize=3, lw=1.0)
        if lo < 0:
            ax.plot(xs[k], 0.012, marker="v", color="black", ms=4)
        ax.text(xs[k], hi + 0.015, f"{v:.2f}", ha="center", va="bottom", fontsize=8)
    ax.axhline(0.5, color="#b5472a", lw=1.0, ls="--")
    ax.text(4.0, 0.5, "pre-registered\nline 0.5", color="#b5472a", fontsize=7, ha="left", va="center")
    ax.set_xlim(-0.6, 5.0)
    ax.set_xticks(list(xs.values()))
    ax.set_xticklabels(["5%", "20%", "5%", "20%"])
    ax.text(0.5, -0.2, "demonstration scale", ha="center", transform=ax.get_xaxis_transform(), fontsize=8)
    ax.text(2.9, -0.2, "full scale", ha="center", transform=ax.get_xaxis_transform(), fontsize=8)
    ax.set_ylabel("corpus-size control effect\nas a fraction of detector 2 effect")
    ax.set_ylim(0, 0.92)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig3_volume_control.pdf"))
    plt.close(fig)
    return vals


def fig_external():
    """Type 1 external counts under each labeller, with exact intervals (Figure 4)."""
    import sys
    sys.path.insert(0, os.path.join(V2, "scripts"))
    from stats_util import clopper_pearson
    names = [("claude_subagent", "R0 (reads repos)"), ("claude-opus-5.5-high", "Claude Opus 5.5"),
             ("chatgpt-luna-5.6-think", "ChatGPT luna 5.6"), ("gemini-4-argon-medium", "Gemini 4 argon")]
    rows = {"narrow": [("our labels", 4, 88)], "broad": [("our labels", 16, 88)]}
    for key, label in names:
        d = json.load(open(os.path.join(V2, "results", "e7a", key, "e7a_agreement_4c.json")))["sensitivity"]["rater"]
        rows["narrow"].append((label, d["narrow"][0], 88))
        rows["broad"].append((label, d["broad"][0], 88))
    oc = json.load(open(os.path.join(V2, "results", "e15_outside_coder.json")))
    coder = {"narrow": (oc["scaled_to_88"]["reachable_unguarded_narrow_ordinary_only"], oc["scaled_to_88_bootstrap_95"]["narrow"]),
             "broad": (oc["scaled_to_88"]["reachable_unguarded_broad"], oc["scaled_to_88_bootstrap_95"]["broad"])}
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.6), sharey=True)
    for ax, (reading, title) in zip(axes, (("narrow", "narrow reading"), ("broad", "broad reading"))):
        for i, (label, k, n) in enumerate(rows[reading]):
            lo, hi = clopper_pearson(k, n)
            y = len(rows[reading]) - i
            ax.errorbar(k / n, y, xerr=[[k / n - lo], [hi - k / n]], fmt="o", ms=4, color=("#1b6ca8" if i == 0 else "#6b6b6b"), capsize=2, lw=1.0)
            ax.text(min(hi + 0.02, 0.98), y, f"{k}/{n}", va="center", fontsize=7.5)
        est, (clo, chi) = coder[reading]
        ax.axhline(0.5, color="#aaaaaa", ls="--", lw=0.8)
        ax.errorbar(est / 88, 0, xerr=[[est / 88 - clo / 88], [chi / 88 - est / 88]], fmt="s", ms=4, color="#b5472a", capsize=2, lw=1.0)
        ax.text(min(chi / 88 + 0.02, 0.98), 0, f"~{est:.0f}/88 (scaled)", va="center", fontsize=7.2)
        ax.set_title(title, fontsize=9)
        ax.set_xlim(0, 1)
        ax.set_xlabel("share of the 88 sampled sites")
        ax.set_yticks(range(len(rows[reading]) + 1))
        ax.set_yticklabels(["outside coder (scaled)"] + [r[0] for r in rows[reading]][::-1], fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig4_external.pdf"))
    plt.close(fig)


if __name__ == "__main__":
    fig_audit_size()
    print(fig_volume())
    fig_external()
