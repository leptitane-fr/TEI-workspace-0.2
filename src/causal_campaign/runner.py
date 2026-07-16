"""Runner — boucle d'observation, séries temporelles (M5), checkpoints de mesures.

Rôle d'EXPÉRIMENTATEUR : fait avancer le moteur tick par tick, applique la
truncature de fenêtre (A11, commodité déclarée), enregistre les séries en
fonction du tick (M5) et déclenche les instruments M1–M4 à des checkpoints.
Aucune information mesurée ne redescend jamais vers le moteur (RÈGLE D'OR).

Les conditions d'arrêt sont des limites de RESSOURCES documentées (A9 :
l'explosion et l'extinction sont des résultats, pas des échecs à masquer) :
  - extinct               : plus aucun messager en vol
  - stalled               : aucune exécution depuis stall_ticks (états périodiques)
  - explosion_events      : max_events dépassé
  - explosion_messengers  : max_messengers dépassé
  - candidate_explosion   : max_candidate_pairs_per_tick dépassé
  - completed             : max_ticks atteint
"""

from __future__ import annotations

import hashlib
import json
import os

from . import journal, measures
from .params import Params
from .seeds import build_engine

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")


def run_id_for(params: Params, label: str) -> str:
    """Identifiant de run déterministe : label + hachage court de la config."""
    digest = hashlib.sha256(json.dumps(params.to_dict(), sort_keys=True).encode()).hexdigest()[:10]
    return f"{label}-{digest}"


def _front_eids(engine) -> list:
    """[M2] Front actif observé : événements d'émission des messagers en vol."""
    return sorted({msg.emit_eid for msg in engine.flight})


def _checkpoint_measures(engine, params: Params, spectral_t_max: int,
                         front_cap: int = 4000, edge_cap: int = 400_000) -> dict:
    """[M2][M3][M4] Mesures de checkpoint sur le front actif + profil du réseau.

    front_cap / edge_cap : limites de RESSOURCES de l'instrument (un front
    explosif de dizaines de milliers de nœuds n'est pas mesurable en Python
    pur) — si dépassées, la mesure est déclarée « skipped », jamais tronquée
    silencieusement.
    """
    events = {e.eid: e for e in engine.events}
    front = _front_eids(engine)
    out = {"tick": engine.tick, "front_size": len(front)}
    if len(front) > front_cap:
        out["M2_growth"] = "skipped_front_too_large"
        out["M4_height_width"] = measures.height_width(events)
        return out
    if len(front) >= 4:
        adj = measures.front_proximity_graph(events, front, params.p)
        sources = measures.even_sources(front, 10)
        growth = measures.bfs_growth(adj, sources)
        out["M2_growth"] = {k: growth[k] for k in ("r", "N", "d_local", "component_sizes")}
        out["M2_plateau"] = measures.plateau(growth["r"], growth["d_local"])
        n_edges = sum(len(v) for v in adj.values()) // 2
        out["front_edges"] = n_edges
        if n_edges <= edge_cap:
            spec = measures.spectral_return(adj, sources, t_max=spectral_t_max)
            out["M3_spectral"] = spec
            out["M3_plateau"] = measures.plateau(spec["t"], spec["d_s"])
        else:
            out["M3_spectral"] = "skipped_too_many_edges"
    out["M4_height_width"] = measures.height_width(events)
    return out


def run(params: Params, label: str, checkpoint_every: int = 0,
        spectral_t_max: int = 96, save: bool = True, note: str = "") -> dict:
    """Exécute un run complet et retourne (et sauvegarde) toutes les données brutes.

    checkpoint_every = 0 : automatique (≈ 10 checkpoints par run).
    """
    params.validate()
    engine = build_engine(params)
    if checkpoint_every <= 0:
        checkpoint_every = max(16, params.max_ticks // 10)

    series = {"tick": [], "n_flight": [], "events_new": [], "events_cum": [],
              "max_depth": [], "candidates": [], "executed": [], "windowed_out": []}
    checkpoints = []
    status = "completed"
    last_exec_tick = 0

    while engine.tick < params.max_ticks:
        rep = engine.step()
        if engine.aborted:
            status = engine.aborted
            break
        removed = engine.apply_window(params.W)  # [A11] truncature d'expérimentateur

        series["tick"].append(rep.tick)
        series["n_flight"].append(len(engine.flight))
        series["events_new"].append(rep.n_executed)
        series["events_cum"].append(len(engine.events))
        series["max_depth"].append(engine.max_depth)
        series["candidates"].append(rep.n_candidate_pairs)
        series["executed"].append(rep.n_executed)
        series["windowed_out"].append(removed)

        if rep.n_executed > 0:
            last_exec_tick = rep.tick

        if rep.tick % checkpoint_every == 0:
            checkpoints.append(_checkpoint_measures(engine, params, spectral_t_max))

        if not engine.flight:
            status = "extinct"
            break
        if len(engine.events) > params.max_events:
            status = "explosion_events"
            break
        if len(engine.flight) > params.max_messengers:
            status = "explosion_messengers"
            break
        if rep.tick - last_exec_tick > params.stall_ticks:
            status = "stalled"
            break

    # Checkpoint final + M1 (intervalle causal) sur l'historique complet
    final_cp = _checkpoint_measures(engine, params, spectral_t_max)
    events = {e.eid: e for e in engine.events}
    children = measures.children_map(events)
    m1 = measures.causal_intervals(events, children)

    rid = run_id_for(params, label)
    result = {
        "run_id": rid,
        "label": label,
        "params": params.to_dict(),
        "status": status,
        "ticks_run": engine.tick,
        "n_events_total": len(engine.events),
        "n_flight_final": len(engine.flight),
        "series": series,                    # M5 : tout en fonction du tick
        "checkpoints": checkpoints,          # M2/M3/M4 au fil du temps (stationnarité)
        "final_checkpoint": final_cp,
        "M1_causal_intervals": m1,
    }

    if save:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(os.path.join(DATA_DIR, rid + ".json"), "w", encoding="utf-8") as fh:
            json.dump(result, fh, ensure_ascii=False)
        journal.append(rid, label, params.to_dict(), status,
                       engine.tick, len(engine.events), len(engine.flight), note)
    return result


def summarize(result: dict) -> str:
    """Résumé texte d'un run pour la console (aucune décision automatique)."""
    cp = result["final_checkpoint"]
    m2p = cp.get("M2_plateau", {})
    m3p = cp.get("M3_plateau", {})
    hw = cp["M4_height_width"]
    lines = [
        f"run {result['run_id']} [{result['status']}] "
        f"ticks={result['ticks_run']} events={result['n_events_total']} "
        f"flight={result['n_flight_final']}",
        f"  M2 front: taille={cp.get('front_size')} plateau d(r)="
        f"{m2p.get('value')} sur [{m2p.get('x_lo')},{m2p.get('x_hi')}] (span x{m2p.get('span_ratio', 0):.1f})"
        if m2p else "  M2 front: n/a",
        f"  M3 spectral: plateau d_s={m3p.get('value')} span x{m3p.get('span_ratio', 0):.1f}" if m3p else "  M3: n/a",
        f"  M4: hauteur={hw['height']} largeur_max={hw['max_width']}",
        f"  M1: pentes locales D(h)={[(h, round(D, 3)) for h, D in result['M1_causal_intervals']['D_local']]}",
    ]
    return "\n".join(lines)
