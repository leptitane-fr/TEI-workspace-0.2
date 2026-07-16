"""GERMES — la Soupe Primordiale.

Milieu propagateur dense exigé par la thermodynamique [A13] : N événements
initiaux (500..1000) « déconnectés », générés par FORMULE EXPLICITE.

INTERDIT ABSOLU (respecté ici) : aucune géométrie — ni grille, ni régularité
dimensionnelle, ni coordonnée. Les états sont dérivés d'un brouillage
algébrique pur (mix64) indexé par un compteur : c'est un nuage sans structure
spatiale. La seule liaison causale est le nœud formel ε (AXIOMES.md,
interprétation n°1), qui sort des fenêtres de parenté dès que le front
dépasse p.

Zéro générateur pseudo-aléatoire [A8] : la formule est fermée et
reproductible ; `seed_salt` (degré de liberté de germe, balayé en M6) décale
la formule pour produire des nuages indépendants.
"""

from __future__ import annotations

from .params import Params
from .substrate import Substrate, mix64

# Constante d'or 64 bits — simple écarteur d'indices dans la formule.
_GOLD = 0x9E3779B97F4A7C15


def sow(sub: Substrate, params: Params) -> int:
    """Ensemence la soupe primordiale : N événements initiaux, chacun émettant
    f messagers [A2] dont l'état est donné par la formule explicite

        state(i, j) = mix64(((i * f + j + 1) * GOLD) XOR mix64(salt)) mod 2^m

    Retourne le nombre de messagers mis en vol.
    """
    if not (500 <= params.seed_N <= 1000):
        raise ValueError("La mission exige un germe massif : 500 <= N <= 1000")
    f = params.f
    mword = (1 << params.m) - 1
    salt = mix64(params.seed_salt)
    n_msg = 0
    for i in range(params.seed_N):
        ev = sub.add_seed_event(tick=0)
        for j in range(f):
            state = mix64(((i * f + j + 1) * _GOLD) ^ salt) & mword
            sub.emit(state, ev.eid)          # [A2] émission porteuse d'état
            n_msg += 1
    return n_msg
