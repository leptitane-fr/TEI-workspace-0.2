#!/usr/bin/env python3
"""Campagne PILOTE — validation bout-en-bout du pipeline sur petites tailles.

Objectif : démontrer que chaque étage (germes M6, balayages M6, contrôles M7,
mesures M1–M5, journal) fonctionne et produit des données brutes exploitables.
Ce pilote NE PRONONCE PAS le verdict : les tailles/durées sont trop petites
(cf. PROTOCOL.md pour la campagne complète : scripts/campaign.py).

Configuration de base : le régime SOUTENU identifié lors du sondage initial
(m=32, s=14, f=2, k=2, p=3, W=16, germe vee) — choisi pour sa STABILITÉ
(critère légitime), jamais pour la valeur d'un exposant (RÈGLE D'OR).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from causal_campaign.params import Params
from causal_campaign.sweep import run_seed_battery, run_param_sweep, run_negative_controls
from causal_campaign.runner import run, summarize

# Caps de ressources du pilote : les runs explosifs avortent vite et sont
# journalisés comme tels (A9 : résultat, pas échec).
BASE = Params(
    m=32, s=14, f=2, k=2, p=3, W=16,
    seed_name="vee",
    max_ticks=3000, max_events=15_000, max_messengers=15_000,
    max_candidate_pairs_per_tick=300_000, stall_ticks=2500,
)


def main() -> None:
    print("=== PILOTE 1/5 : batterie de germes (M6) ===")
    run_seed_battery(BASE, "pilot")

    print("\n=== PILOTE 2/5 : balayage s (seuil de compatibilité, A4) ===")
    run_param_sweep(BASE, "s", [10, 12, 13, 14, 15, 16, 18], "pilot")

    print("\n=== PILOTE 3/5 : balayage W (fenêtre d'expérimentateur, A11) ===")
    run_param_sweep(BASE, "W", [8, 16, 32, 64], "pilot")

    print("\n=== PILOTE 4/5 : balayages p (A6) et f (A2) ===")
    run_param_sweep(BASE, "p", [2, 3, 4], "pilot")
    run_param_sweep(BASE, "f", [2, 3], "pilot")

    print("\n=== PILOTE 5/5 : contrôles négatifs (M7) ===")
    run_negative_controls(BASE, "pilot")

    print("\n=== Témoin structurel : germe antichaîne (gel prouvable par A6) ===")
    res = run(Params(**{**BASE.to_dict(), "seed_name": "antichain2", "stall_ticks": 1500}),
              "pilot-frozen_witness", note="témoin gel A6 (germe déconnecté)")
    print(summarize(res))

    print("\nPilote terminé — données dans data/, journal dans journal/RUNS.md")


if __name__ == "__main__":
    main()
