"""Germes pauvres (A8) — 3 germes viables structurellement différents (3 à 7 événements).

INTERDIT ABSOLU respecté : aucun germe n'encode une géométrie (pas de grille,
tore, triangulation, réseau régulier). Un germe = quelques événements (racines
= données initiales ; les non-racines ont >= 2 causes, conforme A1) + des états
de messagers construits par FORMULE EXPLICITE (hachage déterministe, A8 : zéro
PRNG). Le régime devra se montrer indépendant du germe (M6).

FAIT STRUCTUREL (démontré par le germe témoin « antichain2 ») : la localité
relationnelle A6 interdit tout couplage entre événements sans ancêtre commun.
Un germe fait uniquement de racines déconnectées est donc GELÉ à jamais —
c'est un théorème de l'axiomatique, documenté dans le rapport. Les germes
viables contiennent au moins une relation causale initiale.
"""

from .engine import Engine, mix64, _GOLD
from .params import Params

_C1 = 0xB5297A4D3A2F1E6B
_C2 = 0x68E31DA4B7C15E2D


def _formula_state(a: int, b: int, m: int) -> int:
    """[A8] État de messager de germe : formule explicite mix64(a*GOLD ^ b*C1), tronquée à m bits."""
    return mix64((a * _GOLD) ^ (b * _C1)) & ((1 << m) - 1)


def seed_vee(engine: Engine, params: Params) -> None:
    """[A8] Germe « vee » : 2 racines + 1 événement causé par les deux — 3 événements.

    Structure minimale viable : une seule relation causale, profondeur 1.
    États : formule(C2*(i+1), j+7) pour les racines, formule(C2*31, j+13) pour le fils.
    """
    roots = [engine.add_seed_event((), [_formula_state(_C2 * (i + 1), j + 7, params.m)
                                        for j in range(params.f)]) for i in range(2)]
    engine.add_seed_event(tuple(roots), [_formula_state(_C2 * 31, j + 13, params.m)
                                         for j in range(params.f)])


def seed_wedge4(engine: Engine, params: Params) -> None:
    """[A8] Germe « wedge4 » : 2 racines + 2 fils partageant les mêmes causes — 4 événements.

    Structurellement différent de vee : deux événements frères de profondeur 1
    (largeur initiale 2), autre famille d'états : formule((i+3)^2, 3j+1).
    """
    roots = [engine.add_seed_event((), [_formula_state((i + 3) ** 2, 3 * j + 1, params.m)
                                        for j in range(params.f)]) for i in range(2)]
    for c in range(2):
        engine.add_seed_event(tuple(roots), [_formula_state((c + 11) ** 3, 3 * j + 2, params.m)
                                             for j in range(params.f)])


def seed_braid6(engine: Engine, params: Params) -> None:
    """[A8] Germe « braid6 » : 3 racines, 2 fils croisés, 1 petit-fils — 6 événements.

    Structurellement différent : 3 racines, profondeur 2, recouvrement partiel
    des causes (a,b)->d, (b,c)->e, (d,e)->g. États : formule(17(i+1), 5j+3).
    """
    a, b, c = [engine.add_seed_event((), [_formula_state(17 * (i + 1), 5 * j + 3, params.m)
                                          for j in range(params.f)]) for i in range(3)]
    d = engine.add_seed_event((a, b), [_formula_state(23 * 41, 5 * j + 4, params.m)
                                       for j in range(params.f)])
    e = engine.add_seed_event((b, c), [_formula_state(29 * 43, 5 * j + 6, params.m)
                                       for j in range(params.f)])
    engine.add_seed_event((d, e), [_formula_state(31 * 47, 5 * j + 8, params.m)
                                   for j in range(params.f)])


def seed_antichain2(engine: Engine, params: Params) -> None:
    """[A8] Germe TÉMOIN « antichain2 » : 2 racines sans relation causale.

    Gelé à jamais par A6 (aucun ancêtre commun => aucun test de compatibilité
    possible) — conservé comme démonstration structurelle, PAS comme germe de
    campagne. Sort attendu de tout run : « stalled ».
    """
    for i in range(2):
        engine.add_seed_event((), [_formula_state(i + 1, j + 1, params.m)
                                   for j in range(params.f)])


SEEDS = {
    "vee": seed_vee,
    "wedge4": seed_wedge4,
    "braid6": seed_braid6,
    "antichain2": seed_antichain2,  # témoin gelé (démonstration A6)
}

CAMPAIGN_SEEDS = ("vee", "wedge4", "braid6")  # les >= 3 germes de campagne (M6)


def build_engine(params: Params) -> Engine:
    """[A8] Construit un moteur initialisé avec le germe demandé (tout déterministe)."""
    engine = Engine(params)
    SEEDS[params.seed_name](engine, params)
    return engine
