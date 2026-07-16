"""JOURNALISATION EXHAUSTIVE — tous les runs, y compris ratés.

Chaque run produit :
- data/runs/<run_id>/params.json     (Params + ExperimenterConfig + étiquette)
- data/runs/<run_id>/result.json     (issue, séries de ticks, checkpoints)
- data/runs/<run_id>/*.csv           (données brutes : N_r, d_r, P_t, I_h,
                                      widths, ticks)
- une ligne append-only dans journal/RUNLOG.md

Aucune écriture n'est conditionnelle au succès : EXPLOSION, EXTINCTION et
runs avortés sont journalisés à l'identique (exigence de la mission, A9).
"""

from __future__ import annotations

import hashlib
import json
import os
import time


def repo_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))


def make_run_id(label: str, params_dict: dict) -> str:
    blob = json.dumps(params_dict, sort_keys=True).encode()
    h = hashlib.sha256(blob).hexdigest()[:8]
    stamp = time.strftime("%Y%m%d-%H%M%S")
    return f"{stamp}_{label}_{h}"


def _csv(path: str, header: list[str], rows: list[list]) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(",".join(header) + "\n")
        for row in rows:
            fh.write(",".join(str(x) for x in row) + "\n")


def save_run(run_id: str, label: str, params_dict: dict, cfg_dict: dict,
             result: dict) -> str:
    """Écrit toutes les données brutes du run et retourne le dossier."""
    root = repo_root()
    outdir = os.path.join(root, "data", "runs", run_id)
    os.makedirs(outdir, exist_ok=True)

    with open(os.path.join(outdir, "params.json"), "w", encoding="utf-8") as fh:
        json.dump({"label": label, "params": params_dict,
                   "experimenter_config": cfg_dict}, fh, indent=2)

    with open(os.path.join(outdir, "result.json"), "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)

    # Séries brutes en CSV (dernier checkpoint = état final mesuré).
    ticks = result.get("ticks", [])
    if ticks:
        _csv(os.path.join(outdir, "ticks.csv"),
             ["tick", "n_exec", "n_flight", "n_events", "front_depth",
              "n_truncated"],
             [[t["tick"], t["n_exec"], t["n_flight"], t["n_events"],
               t["front_depth"], t["n_truncated"]] for t in ticks])
    cps = result.get("checkpoints", [])
    if cps:
        last = cps[-1]["measures"]
        _csv(os.path.join(outdir, "N_r.csv"), ["r", "N"],
             [[e["r"], e["N"]] for e in last["m2"].get("N_r", [])])
        _csv(os.path.join(outdir, "d_r.csv"), ["r", "d"],
             [[e["r"], e["d"]] for e in last["m2"].get("d_r", [])])
        _csv(os.path.join(outdir, "P_t.csv"), ["t", "P"],
             [[e["t"], e["P"]] for e in last["m3"].get("P_t", [])])
        _csv(os.path.join(outdir, "I_h.csv"), ["h", "volume"],
             [[e["h"], e["volume"]]
              for e in last["m1"].get("mean_volume_by_h", [])])
        _csv(os.path.join(outdir, "widths.csv"), ["depth", "width"],
             [[e["depth"], e["width"]]
              for e in last["m4"].get("widths", [])])
    return outdir


def append_runlog(run_id: str, label: str, params_dict: dict,
                  result: dict) -> None:
    root = repo_root()
    path = os.path.join(root, "journal", "RUNLOG.md")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    outcome = result.get("outcome", "?")
    summary = result.get("summary", {})
    p = params_dict
    line = ("| {rid} | {label} | m={m} s={s} f={f} k={k} p={pp} W={W} "
            "N={N} sel={salt} | {outcome} | ticks={ticks} | ev={ev} | "
            "d_front={d:.3g} | Dc={Dc:.3g} | ds={ds:.3g} |\n").format(
        rid=run_id, label=label, m=p.get("m"), s=p.get("s"), f=p.get("f"),
        k=p.get("k"), pp=p.get("p"), W=p.get("W"), N=p.get("seed_N"),
        salt=p.get("seed_salt"), outcome=outcome,
        ticks=result.get("final_tick", 0),
        ev=summary.get("n_events", 0),
        d=summary.get("d_front", float("nan")),
        Dc=summary.get("D_causal", float("nan")),
        ds=summary.get("d_s", float("nan")))
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(line)
