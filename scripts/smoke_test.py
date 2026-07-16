#!/usr/bin/env python3
"""Test de bout en bout rapide : germe minimal (500), peu de ticks, toutes
les mesures exercées, run journalisé sous l'étiquette `smoke`."""

import _common  # noqa: F401

from causalnet.journal import append_runlog, make_run_id, save_run
from causalnet.params import ExperimenterConfig, Params
from causalnet.runner import run
from causalnet.substrate import Substrate


def main() -> None:
    params = Params(seed_N=500)
    cfg = ExperimenterConfig(max_ticks=60, checkpoint_every=30,
                             abort_flight=100_000,
                             m1_samples=60, m2_sources=24, m3_sources=12,
                             m3_tmax=64)
    sub = Substrate(params)
    result = run(sub, params, cfg, verbose=True)
    run_id = make_run_id("smoke", params.to_dict())
    outdir = save_run(run_id, "smoke", params.to_dict(), cfg.to_dict(), result)
    append_runlog(run_id, "smoke", params.to_dict(), result)
    s = result["summary"]
    print(f"[{result['outcome']}] tick={result['final_tick']} "
          f"ev={s['n_events']} vol_final={result['ticks'][-1]['n_flight']} "
          f"d_front={s['d_front']:.3f} D_causal={s['D_causal']:.3f} "
          f"d_s={s['d_s']:.3f}")
    print(f"données brutes : {outdir}")
    assert result["final_tick"] > 0
    assert result["checkpoints"], "aucun checkpoint produit"
    print("SMOKE TEST : chaîne complète OK")


if __name__ == "__main__":
    main()
