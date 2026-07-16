#!/usr/bin/env python3
"""M7 — Les trois contrôles négatifs, aux paramètres nominaux.

Chaque contrôle retire un pilier (A4-rareté, A6-localité, A1-causalité) ;
le critère pré-enregistré exige que CHACUN dégrade ou casse le régime.
"""

import argparse
import json
import os

import _common  # noqa: F401

from causalnet.controls import ALL_CONTROLS, make_control
from causalnet.journal import append_runlog, make_run_id, repo_root, save_run
from causalnet.params import ExperimenterConfig, Params
from causalnet.runner import run


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ticks", type=int, default=400)
    ap.add_argument("--abort-flight", type=int, default=200_000)
    args = ap.parse_args()

    params = Params()
    cfg = ExperimenterConfig(max_ticks=args.ticks,
                             abort_flight=args.abort_flight)
    table = []
    for name in ALL_CONTROLS:
        print(f"=== contrôle {name} ===")
        sub = make_control(name, params)
        result = run(sub, params, cfg, verbose=False)
        run_id = make_run_id(name, params.to_dict())
        save_run(run_id, name, params.to_dict(), cfg.to_dict(), result)
        append_runlog(run_id, name, params.to_dict(), result)
        s = result["summary"]
        row = {"control": name, "run_id": run_id,
               "outcome": result["outcome"],
               "final_tick": result["final_tick"], **s}
        table.append(row)
        print(f"  -> [{row['outcome']}] ev={s['n_events']} "
              f"d_front={s['d_front']:.3f} Dc={s['D_causal']:.3f} "
              f"ds={s['d_s']:.3f}")

    outdir = os.path.join(repo_root(), "data", "controls")
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, "controls_table.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(table, fh, indent=2)
    print(f"table des contrôles : {out}")


if __name__ == "__main__":
    main()
