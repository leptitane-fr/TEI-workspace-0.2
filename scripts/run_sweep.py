#!/usr/bin/env python3
"""M6 — Balayage complet des paramètres libres autour d'un point nominal.

Chaque axe est balayé indépendamment (un paramètre bouge, les autres au
nominal), y compris W (A11 : aucun résultat ne doit en dépendre), la taille
et le sel du germe, et les variantes de règles A3/A2/A13. Tous les runs sont
journalisés, ratés compris.

La grille est un choix d'EXPÉRIMENTATEUR (quoi observer) — elle n'encode
aucune cible : les valeurs couvrent simplement chaque axe de bas en haut.
"""

import argparse
import dataclasses
import json
import os

import _common  # noqa: F401

from causalnet.journal import append_runlog, make_run_id, repo_root, save_run
from causalnet.params import ExperimenterConfig, Params
from causalnet.runner import run
from causalnet.substrate import Substrate

# Axes de balayage : chaque entrée = (champ de Params, valeurs).
SWEEP_AXES: dict[str, list] = {
    "m": [16, 24, 32, 48, 64],
    "s": [1, 2, 3, 4, 6, 8],
    "f": [2, 3, 4, 5],
    "k": [2, 3, 4],
    "p": [1, 2, 3, 4, 5],
    "W": [4, 6, 8, 12, 16, 24],          # A11 : indépendance obligatoire
    "dephase_num": [0, 1, 2, 4],          # sévérité A13 (0 = sans déphasage)
    "dephase_den": [16, 32, 64, 128],
    "seed_N": [500, 600, 800, 1000],      # tailles croissantes du germe
    "seed_salt": [0, 1, 2, 3],            # indépendance vis-à-vis du germe
    "rot_rule": ["rotl_step", "rotl_1"],
    "compose_rule": ["fold_xor_rot", "fold_add_rot"],
}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ticks", type=int, default=400)
    ap.add_argument("--abort-flight", type=int, default=200_000)
    ap.add_argument("--axes", nargs="*", default=sorted(SWEEP_AXES),
                    help="sous-ensemble d'axes à balayer")
    args = ap.parse_args()

    nominal = Params()
    cfg = ExperimenterConfig(max_ticks=args.ticks,
                             abort_flight=args.abort_flight)
    table = []
    for axis in args.axes:
        for value in SWEEP_AXES[axis]:
            params = dataclasses.replace(nominal, **{axis: value})
            label = f"sweep_{axis}={value}"
            print(f"=== {label} ===")
            sub = Substrate(params)
            result = run(sub, params, cfg, verbose=False)
            run_id = make_run_id(label, params.to_dict())
            save_run(run_id, label, params.to_dict(), cfg.to_dict(), result)
            append_runlog(run_id, label, params.to_dict(), result)
            s = result["summary"]
            row = {"axis": axis, "value": value, "run_id": run_id,
                   "outcome": result["outcome"],
                   "final_tick": result["final_tick"], **s}
            table.append(row)
            print(f"  -> [{row['outcome']}] ev={s['n_events']} "
                  f"d_front={s['d_front']:.3f} Dc={s['D_causal']:.3f} "
                  f"ds={s['d_s']:.3f}")

    outdir = os.path.join(repo_root(), "data", "sweeps")
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir,
                       "sweep_table_" + "-".join(args.axes) + ".json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(table, fh, indent=2)
    print(f"table de balayage : {out}")


if __name__ == "__main__":
    main()
