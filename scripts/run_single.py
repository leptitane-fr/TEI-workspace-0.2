#!/usr/bin/env python3
"""Un run instrumenté complet : substrat nominal + mesures M1–M5 + journal.

Tous les paramètres exposés sont des degrés de liberté légitimes (params.py)
ou des réglages d'instrument (ExperimenterConfig). Rien d'autre.
"""

import argparse

import _common  # noqa: F401

from causalnet.journal import append_runlog, make_run_id, save_run
from causalnet.params import ExperimenterConfig, Params
from causalnet.runner import run
from causalnet.substrate import Substrate


def build_argparser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__)
    # Degrés de liberté légitimes
    ap.add_argument("--m", type=int, default=32)
    ap.add_argument("--s", type=int, default=4)
    ap.add_argument("--f", type=int, default=3)
    ap.add_argument("--k", type=int, default=2)
    ap.add_argument("--p", type=int, default=3)
    ap.add_argument("--W", type=int, default=8)
    ap.add_argument("--rot-rule", default="rotl_step")
    ap.add_argument("--compose-rule", default="fold_xor_rot")
    ap.add_argument("--dephase-num", type=int, default=1)
    ap.add_argument("--dephase-den", type=int, default=64)
    ap.add_argument("--seed-N", type=int, default=600)
    ap.add_argument("--seed-salt", type=int, default=0)
    # Instrument / ressources
    ap.add_argument("--ticks", type=int, default=400)
    ap.add_argument("--abort-flight", type=int, default=200_000)
    ap.add_argument("--checkpoint-every", type=int, default=50)
    ap.add_argument("--front-layers", type=int, default=4)
    ap.add_argument("--label", default="nominal")
    ap.add_argument("--quiet", action="store_true")
    return ap


def params_from_args(a) -> Params:
    return Params(m=a.m, s=a.s, f=a.f, k=a.k, p=a.p, W=a.W,
                  rot_rule=a.rot_rule, compose_rule=a.compose_rule,
                  dephase_num=a.dephase_num, dephase_den=a.dephase_den,
                  seed_N=a.seed_N, seed_salt=a.seed_salt)


def main() -> None:
    a = build_argparser().parse_args()
    params = params_from_args(a)
    cfg = ExperimenterConfig(max_ticks=a.ticks, abort_flight=a.abort_flight,
                             checkpoint_every=a.checkpoint_every,
                             front_layers=a.front_layers)
    sub = Substrate(params)
    result = run(sub, params, cfg, verbose=not a.quiet)
    run_id = make_run_id(a.label, params.to_dict())
    outdir = save_run(run_id, a.label, params.to_dict(), cfg.to_dict(), result)
    append_runlog(run_id, a.label, params.to_dict(), result)
    s = result["summary"]
    print(f"[{result['outcome']}] tick={result['final_tick']} "
          f"ev={s['n_events']} d_front={s['d_front']:.3f} "
          f"D_causal={s['D_causal']:.3f} d_s={s['d_s']:.3f}")
    print(f"données brutes : {outdir}")


if __name__ == "__main__":
    main()
