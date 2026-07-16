#!/usr/bin/env python3
"""Confrontation des données au CRITÈRE PRÉ-ENREGISTRÉ (PROTOCOLE.md).

Ce script vit du côté RAPPORT : c'est le seul endroit du code, avec le
protocole, où la cible d ≈ 3 a le droit d'exister. Il ne touche jamais au
substrat ; il lit les données brutes déjà journalisées et coche (ou non) les
cases une à une.

Cases du critère :
1. d_front dans [2,7 ; 3,3]
2. plateau (variation < 10 %) sur >= 1 décade de r avant effets de bord
3. stationnarité (M5 : plateau maintenu hors transitoire)
4. d_s concordante (écart < 15 % avec d_front)
5. D_causal ≈ d_front + 1 (tolérance 15 %)
6. robustesse M6 (le régime survit aux balayages ; indépendance en W)
7. M7 : les trois contrôles négatifs dégradent ou cassent

Usage :
  python3 scripts/analyse_verdict.py --run <run_id> [--sweep data/sweeps/sweep_table.json]
                                     [--controls data/controls/controls_table.json]
"""

import argparse
import json
import math
import os

import _common  # noqa: F401

from causalnet.journal import repo_root

D_MIN, D_MAX = 2.7, 3.3          # case 1 (pré-enregistré)
PLATEAU_TOL = 0.10               # case 2
DS_TOL = 0.15                    # case 4
DC_TOL = 0.15                    # case 5


def load_run(run_id: str) -> dict:
    path = os.path.join(repo_root(), "data", "runs", run_id, "result.json")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def check_plateau(d_r: list[dict]) -> dict:
    """Case 2 : cherche la plus longue fenêtre [r1, r2] où d(r) varie de
    moins de PLATEAU_TOL autour de sa médiane ; exige r2/r1 >= 10."""
    best = {"found": False, "r1": None, "r2": None, "d_plateau": float("nan"),
            "decades": 0.0}
    pts = [(e["r"], e["d"]) for e in d_r if e["r"] > 0]
    n = len(pts)
    for i in range(n):
        for j in range(i + 1, n):
            window = [d for _, d in pts[i:j + 1]]
            mid = sorted(window)[len(window) // 2]
            if mid <= 0:
                continue
            if all(abs(d - mid) / abs(mid) < PLATEAU_TOL for d in window):
                decades = math.log10(pts[j][0] / pts[i][0])
                if decades > best["decades"]:
                    best = {"found": decades >= 1.0, "r1": pts[i][0],
                            "r2": pts[j][0], "d_plateau": mid,
                            "decades": decades}
    return best


def check_stationarity(m5: list[dict]) -> dict:
    """Case 3 : d_front stable (< 10 % autour de la médiane) sur la seconde
    moitié des checkpoints (transitoire = première moitié, exclue)."""
    vals = [e["d_front"] for e in m5[len(m5) // 2:]
            if isinstance(e.get("d_front"), (int, float))
            and not math.isnan(e["d_front"])]
    if len(vals) < 2:
        return {"ok": False, "reason": "moins de 2 checkpoints exploitables",
                "values": vals}
    med = sorted(vals)[len(vals) // 2]
    if med == 0:
        return {"ok": False, "reason": "médiane nulle", "values": vals}
    dev = max(abs(v - med) / abs(med) for v in vals)
    return {"ok": dev < PLATEAU_TOL, "median": med, "max_dev": dev,
            "values": vals}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", required=True, help="run_id nominal (M5 long)")
    ap.add_argument("--sweep", default=None)
    ap.add_argument("--controls", default=None)
    args = ap.parse_args()

    result = load_run(args.run)
    last = result["checkpoints"][-1]["measures"]
    grid = {}

    # Case 2 d'abord : le plateau définit d_front (plus robuste que la
    # médiane brute si le plateau existe).
    plateau = check_plateau(last["m2"].get("d_r", []))
    grid["2_plateau_une_decade"] = plateau
    d_front = plateau["d_plateau"] if plateau["found"] else \
        result["summary"]["d_front"]

    grid["1_d_front_dans_fenetre"] = {
        "d_front": d_front,
        "ok": (not math.isnan(d_front)) and D_MIN <= d_front <= D_MAX}

    grid["3_stationnarite"] = check_stationarity(result["m5_series"])

    ds_vals = [e["d_s"] for e in last["m3"].get("d_s", [])]
    mid = ds_vals[len(ds_vals) // 4: (3 * len(ds_vals)) // 4]
    d_s = sorted(mid)[len(mid) // 2] if mid else float("nan")
    ok4 = (not math.isnan(d_s) and not math.isnan(d_front) and d_front != 0
           and abs(d_s - d_front) / abs(d_front) < DS_TOL)
    grid["4_spectrale_concordante"] = {"d_s": d_s, "d_front": d_front,
                                       "ok": ok4}

    dc = last["m1"].get("D_causal", float("nan"))
    ok5 = (not math.isnan(dc) and not math.isnan(d_front)
           and abs(dc - (d_front + 1)) / (abs(d_front) + 1) < DC_TOL)
    grid["5_D_causal_egal_d_plus_1"] = {"D_causal": dc,
                                        "attendu": d_front + 1, "ok": ok5}

    if args.sweep and os.path.exists(args.sweep):
        with open(args.sweep, encoding="utf-8") as fh:
            table = json.load(fh)
        # Robustesse : parmi les runs COMPLETED, d_front reste dans la
        # fenêtre ; l'axe W ne doit montrer aucune dérive systématique.
        completed = [r for r in table if r["outcome"] == "COMPLETED"
                     and not math.isnan(r.get("d_front", float("nan")))]
        in_win = [r for r in completed if D_MIN <= r["d_front"] <= D_MAX]
        w_runs = [r for r in completed if r["axis"] == "W"]
        w_spread = (max(r["d_front"] for r in w_runs)
                    - min(r["d_front"] for r in w_runs)) if len(w_runs) >= 2 \
            else float("nan")
        grid["6_robustesse"] = {
            "n_runs": len(table), "n_completed": len(completed),
            "n_dans_fenetre": len(in_win),
            "W_ecart_d_front": w_spread,
            "ok": (len(completed) > 0 and len(in_win) == len(completed)
                   and not math.isnan(w_spread)
                   and w_spread < PLATEAU_TOL * 3.0)}
    else:
        grid["6_robustesse"] = {"ok": False, "reason": "table M6 absente"}

    if args.controls and os.path.exists(args.controls):
        with open(args.controls, encoding="utf-8") as fh:
            ctrls = json.load(fh)
        rows = []
        for r in ctrls:
            broken = (r["outcome"] != "COMPLETED"
                      or math.isnan(r.get("d_front", float("nan")))
                      or not (D_MIN <= r["d_front"] <= D_MAX))
            rows.append({"control": r["control"], "outcome": r["outcome"],
                         "d_front": r.get("d_front"), "casse": broken})
        grid["7_controles_negatifs"] = {"rows": rows,
                                        "ok": all(x["casse"] for x in rows)
                                        and len(rows) == 3}
    else:
        grid["7_controles_negatifs"] = {"ok": False,
                                        "reason": "table M7 absente"}

    all_ok = all(v.get("ok", v.get("found", False)) for v in grid.values())
    verdict = "OUI (toutes les cases cochées)" if all_ok else \
        "NON ou INDÉTERMINÉ (cases manquantes — voir détail)"
    out = {"run": args.run, "grid": grid, "toutes_cases": all_ok,
           "verdict_mecanique": verdict}
    outdir = os.path.join(repo_root(), "rapport")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, f"analyse_{args.run}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)
    print(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"\nanalyse écrite : {path}")


if __name__ == "__main__":
    main()
