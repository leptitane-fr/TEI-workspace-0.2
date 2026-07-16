"""Degrés de liberté LÉGITIMES de la dynamique — et rien d'autre.

RÈGLE D'OR : aucun champ ne peut encoder une dimension cible, un exposant
visé, un diamètre, ni une quelconque grandeur macroscopique. Ce module est
audité statiquement par scripts/audit_etancheite.py.

La configuration d'expérimentateur (durée, plafond de ressources, cadence de
mesure) vit dans une structure SÉPARÉE (`ExperimenterConfig`) : elle
n'influence jamais les règles, elle borne seulement l'instrument et la
machine (cf. AXIOMES.md, interprétation n°6).
"""

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class Params:
    """Paramètres libres autorisés par la mission (voir AXIOMES.md)."""

    m: int = 32            # [A2] taille du mot d'état (m >= 16)
    s: int = 4             # [A4] seuil de Hamming du prédicat (fixe, jamais piloté)
    f: int = 3             # [A2] fan-out (f >= 2)
    k: int = 2             # [A4] arité d'exécution (k >= 2)
    p: int = 3             # [A6] profondeur de parenté (petite, fixe)
    W: int = 8             # [A11] fenêtre de troncature (balayée en M6)
    rot_rule: str = "rotl_step"        # [A3] variante d'oscillation
    compose_rule: str = "fold_xor_rot"  # [A2] variante de composition
    predicate_rule: str = "hamming_pivot"  # [A4] structure du prédicat
    dephase_num: int = 1   # [A13] sévérité = densité * num // den (bits de masque)
    dephase_den: int = 64  # [A13]
    seed_N: int = 600      # taille de la soupe primordiale (500..1000 exigé)
    seed_salt: int = 0     # variante de la formule explicite du germe (M6)

    def __post_init__(self) -> None:
        # Bornes structurelles imposées par l'axiomatique elle-même.
        if self.m < 16:
            raise ValueError("A2 exige m >= 16")
        if self.f < 2:
            raise ValueError("A2 exige f >= 2")
        if self.k < 2:
            raise ValueError("A4 exige k >= 2")
        if not (0 <= self.s <= self.m):
            raise ValueError("A4 : 0 <= s <= m")
        if self.p < 1:
            raise ValueError("A6 : p >= 1")
        if self.W < 1:
            raise ValueError("A11 : W >= 1")
        if self.dephase_num < 0 or self.dephase_den < 1:
            raise ValueError("A13 : sévérité proportionnelle positive")

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ExperimenterConfig:
    """Configuration d'INSTRUMENT / de ressources — hors dynamique.

    Aucun de ces champs n'est lu par le substrat pour décider d'une règle :
    - max_ticks     : durée d'observation (l'expérimentateur coupe le courant) ;
    - abort_flight  : plafond de ressources machine (messagers en vol) ; s'il
                      est franchi le run est ARRÊTÉ et journalisé EXPLOSION
                      (A9 : la dynamique n'est jamais freinée, on cesse
                      simplement d'observer) ;
    - abort_events  : même statut, sur le nombre d'événements (protège la
                      mémoire de la machine — l'historique est l'instrument) ;
    - checkpoint_every : cadence des mesures M5 ;
    - front_layers  : épaisseur (en couches) du front mesuré en M2/M3 ;
    - m1_samples, m2_sources, m3_sources, m3_tmax : tailles d'échantillonnage
      DÉTERMINISTE (par pas constant) des instruments.
    """

    max_ticks: int = 400
    abort_flight: int = 200_000
    abort_events: int = 400_000
    checkpoint_every: int = 50
    front_layers: int = 4
    m1_samples: int = 200
    m2_sources: int = 64
    m3_sources: int = 32
    m3_tmax: int = 256

    def to_dict(self) -> dict:
        return asdict(self)
