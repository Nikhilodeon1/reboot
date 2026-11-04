"""Figures for the v2 paper, drawn from archived aggregate results only.

    python v2/paper/make_figs.py

Fig. 2 reads v2/results/e3_d1_audit_size.json (E3). Fig. 3 reads the round-1 results for detector 2 (demonstration and
full scale). Nothing here recomputes a statistic; r2/r1 is the ratio of the arm means in the archived files.
"""
import os
import json

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
    fig, ax = plt.subplots(figsize=(4.6, 3.0))
    for key, label, col in names:
        rows = d["cases"][key]["rows"]
        n = [r["n"] for r in rows]
        ax.plot(n, [r["p_hat"] for r in rows], "-", color=col, lw=1.2)
        ax.errorbar(n, [r["p_obs"] for r in rows],
                    yerr=[[r["p_obs"] - r["cp95"][0] for r in rows], [r["cp95"][1] - r["p_obs"] for r in rows]],
                    fmt="o", ms=3.5, color=col, capsize=2, lw=0.9, label=label)
    ax.axhspan(0.05, 0.95, color="#000000", alpha=0.04, lw=0)
    ax.set_xscale("log")
    ax.set_xlabel("audit size n (stays per audit draw)")
    ax.set_ylabel("flag probability, kappa < 0.60")
    ax.set_ylim(-0.03, 1.03)
    ax.legend(frameon=False, fontsize=7.5, loc="center", bbox_to_anchor=(0.62, 0.76))
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
    full = os.path.join(R1, "tier2_local.json")
    vals = {("Demonstration", 5): ratio(demo, "demo", 5), ("Demonstration", 20): ratio(demo, "demo", 20),
            ("Full", 5): ratio(full, "full", 5), ("Full", 20): ratio(full, "full", 20)}
    fig, ax = plt.subplots(figsize=(3.6, 2.8))
    xs = {("Demonstration", 5): 0, ("Demonstration", 20): 1, ("Full", 5): 2.4, ("Full", 20): 3.4}
    cols = {"Demonstration": "#7f9fbf", "Full": "#1b6ca8"}
    for k, v in vals.items():
        ax.bar(xs[k], v, width=0.8, color=cols[k[0]])
        ax.text(xs[k], v + 0.02, f"{v:.2f}", ha="center", fontsize=8)
    ax.axhline(0.5, color="#b5472a", lw=1.0, ls="--")
    ax.text(3.9, 0.51, "pre-registered line 0.5", color="#b5472a", fontsize=7, ha="right", va="bottom")
    ax.set_xticks(list(xs.values()))
    ax.set_xticklabels(["5%", "20%", "5%", "20%"])
    ax.text(0.5, -0.2, "demonstration scale", ha="center", transform=ax.get_xaxis_transform(), fontsize=8)
    ax.text(2.9, -0.2, "full scale", ha="center", transform=ax.get_xaxis_transform(), fontsize=8)
    ax.set_ylabel("corpus-size control effect\nas a fraction of detector 2 effect")
    ax.set_ylim(0, 0.85)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig3_volume_control.pdf"))
    plt.close(fig)
    return vals


if __name__ == "__main__":
    fig_audit_size()
    print(fig_volume())
