#!/usr/bin/env python3
"""Analyse de campagne — PHASE DE RAPPORT.

Lit toutes les données brutes de data/*.json et produit :
  - data/summary.csv           table de balayage complète (une ligne par run)
  - reports/ANALYSIS.md        synthèse par run + confrontation aux critères

C'est ICI, et seulement ici, que les critères pré-enregistrés de PROTOCOL.md
(d ∈ [2,7;3,3], concordances < 15 %, décade, stationnarité, contrôles) sont
comparés aux mesures publiées. Aucun code de génération ou de mesure ne les
contient. Ce script ne relance ni ne modifie aucun run.
"""

import csv
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
REPORTS = os.path.join(ROOT, "reports")

# Critères pré-enregistrés (PROTOCOL.md) — utilisés uniquement en rapport.
TARGET_LO, TARGET_HI = 2.7, 3.3
CONCORDANCE = 0.15
DECADE = 10.0
PLATEAU_TOL = 0.10


def classify_fate(run: dict) -> str:
    """Sort du run, du point de vue de l'expérimentateur."""
    st = run["status"]
    if st in ("extinct",):
        return "extinction"
    if st in ("stalled",):
        return "gel"
    if st.startswith("explosion") or st == "candidate_explosion":
        return "explosion"
    series = run.get("series", {})
    ex = series.get("executed", [])
    if not ex or not any(ex):
        return "gel"
    tail = ex[-max(1, len(ex) // 10):]
    return "soutenu" if any(tail) else "moribond"


def stationarity(run: dict) -> dict:
    """[M5] Dérive du plateau d(r) du front à travers les checkpoints.

    transient = premier checkpoint dont la valeur reste dans ±10 % de la valeur
    finale ; tenue = (dernier tick − tick du transitoire) / tick du transitoire.
    """
    vals = []
    for cp in run.get("checkpoints", []) + [run.get("final_checkpoint", {})]:
        plat = cp.get("M2_plateau")
        if isinstance(plat, dict) and plat.get("value") is not None:
            vals.append((cp["tick"], plat["value"]))
    if len(vals) < 3:
        return {"n_checkpoints": len(vals), "transient_tick": None, "hold_ratio": None,
                "final_value": vals[-1][1] if vals else None, "series": vals}
    final = vals[-1][1]
    transient = None
    for t, v in vals:
        if final and abs(v - final) <= PLATEAU_TOL * abs(final):
            ok = all(abs(v2 - final) <= PLATEAU_TOL * abs(final) for t2, v2 in vals if t2 >= t)
            if ok:
                transient = t
                break
    hold = (vals[-1][0] - transient) / transient if transient else None
    return {"n_checkpoints": len(vals), "transient_tick": transient,
            "hold_ratio": hold, "final_value": final, "series": vals}


def causal_D_tail(run: dict):
    """[M1] Moyenne des pentes locales D(h) sur la moitié supérieure des hauteurs."""
    dl = run.get("M1_causal_intervals", {}).get("D_local", [])
    if not dl:
        return None
    tail = dl[len(dl) // 2:]
    return sum(D for _, D in tail) / len(tail)


def criteria(run: dict, stat: dict) -> dict:
    """Confrontation aux critères pré-enregistrés (rapport uniquement)."""
    out = {}
    cp = run.get("final_checkpoint", {})
    m2 = cp.get("M2_plateau") if isinstance(cp.get("M2_plateau"), dict) else {}
    m3 = cp.get("M3_plateau") if isinstance(cp.get("M3_plateau"), dict) else {}
    d = m2.get("value")
    out["d_front"] = d
    out["c1_d_in_target"] = d is not None and TARGET_LO <= d <= TARGET_HI
    out["c1b_decade"] = (m2.get("span_ratio") or 0) >= DECADE
    out["c2_stationnaire"] = (stat.get("hold_ratio") or 0) >= 10.0
    ds = m3.get("value")
    out["d_s"] = ds
    out["c3_spectral"] = (d is not None and ds is not None and d != 0
                          and abs(ds - d) <= CONCORDANCE * abs(d))
    Dc = causal_D_tail(run)
    out["D_causal_tail"] = Dc
    out["c4_causal"] = (d is not None and Dc is not None
                        and abs(Dc - (d + 1)) <= CONCORDANCE * abs(d + 1))
    return out


def row_for(run: dict) -> dict:
    p = run["params"]
    stat = stationarity(run)
    crit = criteria(run, stat)
    cp = run.get("final_checkpoint", {})
    hw = cp.get("M4_height_width", {})
    return {
        "run_id": run["run_id"], "label": run["label"], "status": run["status"],
        "fate": classify_fate(run),
        "seed": p["seed_name"], "m": p["m"], "s": p["s"], "f": p["f"], "k": p["k"],
        "p": p["p"], "W": p["W"], "pred": p["predicate"], "osc": p["osc_rule"],
        "comp": p["compose_rule"],
        "ctrl": ("trivial" if p.get("control_trivial_predicate") else
                 "p_inf" if p.get("control_p_infinite") else
                 "no_caus" if p.get("control_ignore_causality") else ""),
        "ticks": run["ticks_run"], "events": run["n_events_total"],
        "flight": run["n_flight_final"], "front": cp.get("front_size"),
        "height": hw.get("height"), "max_width": hw.get("max_width"),
        "d_front": crit["d_front"], "d_span": (cp.get("M2_plateau") or {}).get("span_ratio")
        if isinstance(cp.get("M2_plateau"), dict) else None,
        "d_s": crit["d_s"], "D_causal": crit["D_causal_tail"],
        "transient": stat["transient_tick"], "hold": stat["hold_ratio"],
        "c1_target": crit["c1_d_in_target"], "c1b_decade": crit["c1b_decade"],
        "c2_stat": crit["c2_stationnaire"], "c3_spec": crit["c3_spectral"],
        "c4_caus": crit["c4_causal"],
    }


def fmt(v):
    if v is None:
        return "—"
    if isinstance(v, bool):
        return "✓" if v else "✗"
    if isinstance(v, float):
        return f"{v:.3g}"
    return str(v)


def main() -> None:
    pattern = sys.argv[1] if len(sys.argv) > 1 else "*"
    files = sorted(glob.glob(os.path.join(DATA, f"{pattern}.json")))
    rows = []
    for path in files:
        with open(path, encoding="utf-8") as fh:
            try:
                rows.append(row_for(json.load(fh)))
            except (json.JSONDecodeError, KeyError) as exc:
                print(f"ignoré {os.path.basename(path)}: {exc}", file=sys.stderr)

    os.makedirs(REPORTS, exist_ok=True)
    if rows:
        with open(os.path.join(DATA, "summary.csv"), "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)

    cols = ["run_id", "fate", "status", "seed", "m", "s", "f", "k", "p", "W", "pred",
            "ctrl", "ticks", "events", "front", "height", "max_width",
            "d_front", "d_span", "d_s", "D_causal", "transient", "hold",
            "c1_target", "c1b_decade", "c2_stat", "c3_spec", "c4_caus"]
    lines = ["# ANALYSE DE CAMPAGNE (générée par scripts/analyze.py)", "",
             f"{len(rows)} runs analysés. Critères : voir PROTOCOL.md ; "
             "c1 = d∈[2,7;3,3], c1b = plateau ≥ 1 décade, c2 = tenue ≥ 10×transitoire, "
             "c3 = |d_s−d| < 15 %, c4 = |D_causal−(d+1)| < 15 %.", "",
             "| " + " | ".join(cols) + " |",
             "|" + "---|" * len(cols)]
    for r in rows:
        lines.append("| " + " | ".join(fmt(r[c]) for c in cols) + " |")

    fates = {}
    for r in rows:
        fates[r["fate"]] = fates.get(r["fate"], 0) + 1
    lines += ["", "## Répartition des sorts", ""]
    lines += [f"- **{k}** : {v} runs" for k, v in sorted(fates.items())]
    full_pass = [r for r in rows if r["c1_target"] and r["c1b_decade"] and r["c2_stat"]
                 and r["c3_spec"] and r["c4_caus"] and not r["ctrl"]]
    lines += ["", f"## Runs satisfaisant c1–c4 (hors contrôles) : {len(full_pass)}", ""]
    lines += [f"- `{r['run_id']}`" for r in full_pass]

    with open(os.path.join(REPORTS, "ANALYSIS.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"{len(rows)} runs → reports/ANALYSIS.md + data/summary.csv")
    print("sorts :", fates)
    print("candidats c1–c4 :", [r["run_id"] for r in full_pass] or "aucun")


if __name__ == "__main__":
    main()
