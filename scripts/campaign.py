#!/usr/bin/env python3
"""Campagne COMPLÈTE — celle qui alimente le verdict (cf. PROTOCOL.md).

Étages, dans l'ordre (chaque étage journalise TOUS ses runs) :
  1. Batterie de germes (>= 3, M6) sur chaque configuration de base retenue
  2. Balayage complet de chaque paramètre libre (M6) : m, s, f, k, p,
     règle d'oscillation, règle de composition, prédicat
  3. Balayage de W (A11) : indépendance à la fenêtre obligatoire
  4. Tailles croissantes (max_ticks / max_events) aussi loin que possible
  5. Contrôles négatifs (M7) sur chaque régime candidat

Usage : python3 scripts/campaign.py [stage]   (stage ∈ 1..5, défaut : tout)

RÈGLE D'OR : si un régime stationnaire apparaît, on le documente quelle que
soit sa dimension. Aucune configuration n'est retenue ou rejetée sur la
valeur d'un exposant — uniquement sur l'existence d'un plateau stationnaire.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from causal_campaign.params import Params
from dataclasses import replace
from causal_campaign.sweep import run_seed_battery, run_param_sweep, run_negative_controls

# Configurations de base de la campagne. À enrichir au fil des découvertes —
# critère d'ajout : conformité axiomatique + existence d'un régime soutenu.
BASES = {
    # Régime soutenu identifié au pilote (filament) — point de départ.
    "filament": Params(m=32, s=14, f=2, k=2, p=3, W=16, seed_name="vee",
                       max_ticks=20_000, max_events=100_000, max_messengers=100_000,
                       max_candidate_pairs_per_tick=1_000_000, stall_ticks=4096, max_wall_seconds=240),
    # Familles alternatives à explorer (états larges, prédicat par blocs, k=3).
    "wide_state": Params(m=64, s=24, f=2, k=2, p=3, W=16, seed_name="vee",
                         max_ticks=20_000, max_events=100_000, max_messengers=100_000,
                         max_candidate_pairs_per_tick=1_000_000, stall_ticks=8192, max_wall_seconds=240),
    "blocks": Params(m=32, s=2, f=2, k=2, p=3, W=16, predicate="block_zero", seed_name="vee",
                     max_ticks=20_000, max_events=100_000, max_messengers=100_000,
                     max_candidate_pairs_per_tick=1_000_000, stall_ticks=4096, max_wall_seconds=240),
    "triadic": Params(m=32, s=12, f=3, k=3, p=3, W=16, seed_name="vee",
                      max_ticks=20_000, max_events=100_000, max_messengers=100_000,
                      max_candidate_pairs_per_tick=1_000_000, stall_ticks=4096, max_wall_seconds=240),
}

SWEEPS = {
    "m": [16, 24, 32, 48, 64],
    "s": [8, 10, 12, 13, 14, 15, 16, 18, 20, 24],
    "f": [2, 3, 4],
    "k": [2, 3],
    "p": [1, 2, 3, 4, 5],
    "osc_rule": ["rot_birth", "rot1_xor"],
    "compose_rule": ["fold_rot_xor", "fold_mul_add"],
    "predicate": ["hamming", "block_zero"],
}

W_SWEEP = [4, 8, 16, 32, 64, 128]


def stage1() -> None:
    for name, base in BASES.items():
        run_seed_battery(base, f"camp-{name}")


def stage2() -> None:
    for name, base in BASES.items():
        for pname, values in SWEEPS.items():
            run_param_sweep(base, pname, values, f"camp-{name}")


def stage3() -> None:
    for name, base in BASES.items():
        run_param_sweep(base, "W", W_SWEEP, f"camp-{name}")


def stage4() -> None:
    for name, base in BASES.items():
        big = replace(base, max_wall_seconds=600)
        run_param_sweep(big, "max_ticks", [5_000, 20_000, 80_000, 320_000], f"camp-{name}-size")


def stage5() -> None:
    for name, base in BASES.items():
        run_negative_controls(base, f"camp-{name}")


STAGES = {1: stage1, 2: stage2, 3: stage3, 4: stage4, 5: stage5}


def main() -> None:
    wanted = [int(a) for a in sys.argv[1:]] or [1, 3, 5, 2, 4]
    for st in wanted:
        print(f"\n========== CAMPAGNE — ÉTAGE {st} ==========")
        STAGES[st]()


if __name__ == "__main__":
    main()
