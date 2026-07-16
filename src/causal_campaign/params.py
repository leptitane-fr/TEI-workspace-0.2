"""Paramètres d'un run — uniquement les degrés de liberté légitimes + truncatures d'expérimentateur.

Degrés de liberté légitimes (cf. PROTOCOL.md) : m, s, f, k, p, W,
règle d'oscillation (A3), règle de composition (A2), prédicat (A4), germe.

RÈGLE D'OR : aucun paramètre n'encode un exposant cible, une dimension,
un diamètre ou une correction macroscopique. Les caps max_* sont des limites
de RESSOURCES d'expérimentateur (fin d'observation), jamais des règles du
substrat : ils arrêtent le run, ils ne modifient jamais la dynamique.
"""

from dataclasses import dataclass, field, asdict


@dataclass(frozen=True)
class Params:
    # --- Degrés de liberté du substrat ---
    m: int = 32               # [A2] largeur d'état en bits (>= 16)
    s: int = 8                # [A4] seuil du prédicat de compatibilité (fixe, jamais piloté)
    f: int = 3                # [A2] fan-out : messagers émis par événement (>= 2)
    k: int = 2                # [A4] arité d'exécution (>= 2)
    p: int = 3                # [A6] profondeur de parenté pour la localité relationnelle
    W: int = 16               # [A11] fenêtre d'expérimentateur (à balayer, pas une règle)
    osc_rule: str = "rot_birth"        # [A3] "rot_birth" | "rot1_xor"
    compose_rule: str = "fold_rot_xor"  # [A2] "fold_rot_xor" | "fold_mul_add"
    predicate: str = "hamming"          # [A4] "hamming" | "block_zero"
    seed_name: str = "vee"              # [A8] germe pauvre : "vee" | "wedge4" | "braid6" (+ témoin "antichain2")

    # --- Contrôles négatifs M7 (interrupteurs d'expérimentateur) ---
    control_trivial_predicate: bool = False  # [M7-i]  compatibilité toujours vraie
    control_p_infinite: bool = False         # [M7-ii] localité retirée (p = infini)
    control_ignore_causality: bool = False   # [M7-iii] couplages hors de tout lien de parenté

    # --- Truncatures de ressources d'expérimentateur (PAS des règles, cf. A9/A11/A12) ---
    max_ticks: int = 2000
    max_events: int = 200_000
    max_messengers: int = 300_000
    max_candidate_pairs_per_tick: int = 2_000_000  # abandon documenté si dépassé ("explosion")
    stall_ticks: int = 4096   # arrêt si aucune exécution pendant N ticks (états périodiques => mort prouvable)
    max_wall_seconds: int = 0  # plafond de temps mur par run (0 = aucun) — arrêt d'OBSERVATION
                               # journalisé "wall_time" ; ne modifie jamais la dynamique

    def validate(self) -> None:
        assert self.m >= 16, "A2 exige m >= 16"
        assert self.f >= 2, "A2 exige f >= 2"
        assert self.k >= 2, "A4 exige k >= 2"
        assert self.s >= 0
        assert self.p >= 1, "A6 exige p petit mais >= 1"
        assert self.W >= 1

    def to_dict(self) -> dict:
        return asdict(self)
