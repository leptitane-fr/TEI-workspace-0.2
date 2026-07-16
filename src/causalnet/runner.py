"""ORCHESTRATEUR de runs instrumentés.

Sépare strictement les rôles :
- le substrat avance tick par tick (aveugle) ;
- l'expérimentateur décide QUAND observer (checkpoints M5) et QUAND cesser
  d'observer (durée, extinction, plafond de ressources) — jamais COMMENT la
  dynamique évolue ;
- les instruments (measure.py) lisent l'historique en lecture seule.

Issues possibles d'un run (toutes journalisées, A9) :
- COMPLETED  : durée d'observation atteinte ;
- EXTINCTION : plus aucun messager en vol ;
- EXPLOSION  : population > abort_flight (arrêt de ressources, cf.
               AXIOMES.md n°6) ;
- STALLED    : plus aucune exécution depuis longtemps mais des messagers
               tournent encore (régime gelé, détecté par l'observateur).
"""

from __future__ import annotations

import math
import statistics

from . import measure
from .params import ExperimenterConfig, Params
from .seeds import sow
from .substrate import Substrate


def _median_or_nan(vals: list[float]) -> float:
    return statistics.median(vals) if vals else float("nan")


def summarize(checkpoint: dict, n_events: int) -> dict:
    """Résumé scalaire d'un checkpoint pour le journal : exposant de
    croissance médian du front (fenêtre médiane de r), D_causal, d_s médian.
    Les séries complètes restent dans result.json (le résumé n'écrase rien).
    """
    d_r = checkpoint["m2"].get("d_r", [])
    # Fenêtre médiane : on écarte les 2 premiers r (granularité) et le
    # dernier quart (effets de bord) — convention d'instrument, déclarée.
    core = [e["d"] for e in d_r[2: max(3, (3 * len(d_r)) // 4)]]
    d_s_series = checkpoint["m3"].get("d_s", [])
    mid = d_s_series[len(d_s_series) // 4: (3 * len(d_s_series)) // 4]
    return {
        "n_events": n_events,
        "d_front": _median_or_nan(core),
        "D_causal": checkpoint["m1"].get("D_causal", float("nan")),
        "d_s": _median_or_nan([e["d_s"] for e in mid]),
        "front_nodes": checkpoint["m2"].get("n_nodes", 0),
        "height": checkpoint["m4"].get("height", 0),
        "width_max": checkpoint["m4"].get("width_max", 0),
    }


def run(substrate: Substrate, params: Params, cfg: ExperimenterConfig,
        verbose: bool = False) -> dict:
    """Exécute un run instrumenté complet et retourne le résultat brut."""
    n0 = sow(substrate, params)
    ticks: list[dict] = []
    checkpoints: list[dict] = []
    outcome = "COMPLETED"
    last_exec_tick = 0

    for _ in range(cfg.max_ticks):
        st = substrate.step()
        ticks.append(st.to_dict())
        if st.n_exec > 0:
            last_exec_tick = st.tick
        if verbose and st.tick % 20 == 0:
            print(f"  tick {st.tick:5d}  vol={st.n_flight:7d} "
                  f"ev={st.n_events:7d} front={st.front_depth:4d} "
                  f"exec={st.n_exec}")
        if st.tick % cfg.checkpoint_every == 0:
            log = measure.extract_log(substrate)
            cp = measure.full_checkpoint(log, params.p, cfg)
            checkpoints.append({"tick": st.tick, "measures": cp,
                                "summary": summarize(cp, st.n_events)})
        if st.n_flight == 0:
            outcome = "EXTINCTION"
            break
        if st.n_flight > cfg.abort_flight:
            # Arrêt de RESSOURCES (instrument) — la dynamique n'a jamais été
            # freinée ; l'explosion est un résultat documenté (A9).
            outcome = "EXPLOSION"
            break
        if st.tick - last_exec_tick > 4 * params.m:
            # Plus aucune exécution depuis > 4 périodes maximales : régime
            # gelé (les états ne peuvent plus se recroiser autrement).
            outcome = "STALLED"
            break

    # Checkpoint final systématique (même pour les runs avortés).
    log = measure.extract_log(substrate)
    final_cp = measure.full_checkpoint(log, params.p, cfg)
    n_events = len(log) - 1
    checkpoints.append({"tick": substrate.tick, "measures": final_cp,
                        "summary": summarize(final_cp, n_events)})

    m5 = [{"tick": c["tick"], **c["summary"]} for c in checkpoints]
    return {
        "outcome": outcome,
        "final_tick": substrate.tick,
        "n_seed_messengers": n0,
        "ticks": ticks,
        "checkpoints": checkpoints,
        "m5_series": m5,                     # M5 : mesures vs tick
        "summary": checkpoints[-1]["summary"],
    }
