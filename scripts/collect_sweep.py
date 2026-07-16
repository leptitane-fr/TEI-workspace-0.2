#!/usr/bin/env python3
"""Reconstruit la table M6 complète depuis les runs journalisés.

Balaye data/runs/*/ ; tout run dont l'étiquette est `sweep_<axe>=<valeur>`
entre dans la table fusionnée data/sweeps/sweep_table.json (une ligne par
run, le plus récent gagnant en cas de doublon d'étiquette).
"""

import json
import os

import _common  # noqa: F401

from causalnet.journal import repo_root


def main() -> None:
    runs_dir = os.path.join(repo_root(), "data", "runs")
    by_label: dict[str, dict] = {}
    for run_id in sorted(os.listdir(runs_dir)):
        pdir = os.path.join(runs_dir, run_id)
        try:
            with open(os.path.join(pdir, "params.json"), encoding="utf-8") as fh:
                meta = json.load(fh)
            with open(os.path.join(pdir, "result.json"), encoding="utf-8") as fh:
                result = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue
        label = meta.get("label", "")
        if not label.startswith("sweep_") or "=" not in label:
            continue
        axis, value = label[len("sweep_"):].split("=", 1)
        row = {"axis": axis, "value": value, "run_id": run_id,
               "outcome": result["outcome"],
               "final_tick": result["final_tick"],
               **result["summary"]}
        by_label[label] = row  # tri par run_id : le plus récent écrase

    table = sorted(by_label.values(),
                   key=lambda r: (r["axis"], str(r["value"])))
    outdir = os.path.join(repo_root(), "data", "sweeps")
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, "sweep_table.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(table, fh, indent=2)
    print(f"{len(table)} runs de balayage fusionnés -> {out}")
    for r in table:
        print(f"  {r['axis']}={r['value']:>12} [{r['outcome']:<10}] "
              f"ev={r['n_events']:>7} d_front={r['d_front']!s:>8} "
              f"Dc={r['D_causal']!s:>8}")


if __name__ == "__main__":
    main()
