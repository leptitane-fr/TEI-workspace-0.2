#!/usr/bin/env python3
"""Génère les tables markdown du rapport de verdict depuis les données
brutes journalisées (aucun recalcul : simple mise en forme)."""

import json
import math
import os

import _common  # noqa: F401

from causalnet.journal import repo_root


def fmt(x, nd=3):
    if x is None:
        return "—"
    if isinstance(x, float) and math.isnan(x):
        return "n.m."  # non mesurable
    if isinstance(x, float):
        return f"{x:.{nd}g}"
    return str(x)


def main() -> None:
    root = repo_root()
    with open(os.path.join(root, "data", "sweeps", "sweep_table.json"),
              encoding="utf-8") as fh:
        sweep = json.load(fh)
    with open(os.path.join(root, "data", "controls",
                           "controls_table.json"), encoding="utf-8") as fh:
        controls = json.load(fh)

    print("## Table M6 (balayage des paramètres libres)\n")
    print("| axe | valeur | issue | ticks | événements | d_front | D_causal |")
    print("|---|---|---|---|---|---|---|")
    axis_order = ["s", "m", "f", "k", "p", "W", "dephase_num", "dephase_den",
                  "seed_N", "seed_salt", "rot_rule", "compose_rule"]
    def key(r):
        ax = r["axis"]
        i = axis_order.index(ax) if ax in axis_order else 99
        try:
            v = float(str(r["value"]).replace("_long", ""))
        except ValueError:
            v = 0.0
        return (i, v, str(r["value"]))
    for r in sorted(sweep, key=key):
        print(f"| {r['axis']} | {r['value']} | {r['outcome']} "
              f"| {r['final_tick']} | {r['n_events']} "
              f"| {fmt(r['d_front'])} | {fmt(r['D_causal'])} |")

    print("\n## Table M7 (contrôles négatifs)\n")
    print("| contrôle | issue | ticks | événements | d_front | D_causal |")
    print("|---|---|---|---|---|---|")
    for r in controls:
        print(f"| {r['control']} | {r['outcome']} | {r['final_tick']} "
              f"| {r['n_events']} | {fmt(r['d_front'])} "
              f"| {fmt(r['D_causal'])} |")

    print("\n## Runs de référence et sondes combinées\n")
    print("| run | issue | ticks | événements | hauteur | nœuds de front "
          "| D_causal |")
    print("|---|---|---|---|---|---|---|")
    runs_dir = os.path.join(root, "data", "runs")
    for rid in sorted(os.listdir(runs_dir)):
        if not ("nominal_v2" in rid or "combo" in rid or "s=7" in rid):
            continue
        try:
            with open(os.path.join(runs_dir, rid, "result.json"),
                      encoding="utf-8") as fh:
                res = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue
        s = res["summary"]
        print(f"| {rid.split('_', 1)[1]} | {res['outcome']} "
              f"| {res['final_tick']} | {s['n_events']} | {s['height']} "
              f"| {s['front_nodes']} | {fmt(s['D_causal'])} |")


if __name__ == "__main__":
    main()
