#!/usr/bin/env python3
"""CERTIFICAT DE GEL EXACT (instrument d'analyse, lecture seule).

Pour un état gelé (plus aucune exécution), ce script PROUVE que le gel est
éternel, sans borne de temps, par l'argument suivant :

Soit deux messagers en vol d'états a0, b0 et de pas de rotation sa, sb
(fixes à vie, A3). Au tick t (relatif), leurs états sont
    a(t) = rotl(a0, t*sa mod m),   b(t) = rotl(b0, t*sb mod m).
La rotation commune préserve la distance de Hamming :
    H(t) = popcount( a0 XOR rotl(b0, t*(sb-sa) mod m) ).
H ne dépend de t qu'à travers delta(t) = t*(sb-sa) mod m, qui parcourt
exactement le sous-groupe engendré par g = gcd(sb-sa, m) dans Z_m.
Le minimum de H sur ce sous-groupe est donc calculable EXACTEMENT en au plus
m/g évaluations.

Si, pour TOUTE paire de messagers testables au sens A6 (godet commun),
min H > s, alors aucun événement ne peut plus jamais naître : l'état est un
point fixe de la dynamique (seules les phases tournent). Le certificat est
rigoureux car en l'absence d'exécution, ni la flotte, ni les émetteurs, ni
les godets ne changent — la troncature A11 ne retire rien de plus (le front
n'avance plus).

Usage : python3 scripts/certif_gel.py [--ticks 800] [+ tout paramètre libre]
Rejoue le run (déterminisme A8), détecte le gel, puis certifie.
"""

import math

import _common  # noqa: F401

from causalnet.seeds import sow
from causalnet.substrate import Substrate, rotl

from run_single import build_argparser, params_from_args


def min_hamming_over_cycle(a0: int, sa: int, b0: int, sb: int, m: int) -> int:
    """Min exact de H sur le sous-groupe {t*(sb-sa) mod m} de Z_m."""
    d = (sb - sa) % m
    g = math.gcd(d, m) if d else m
    best = m + 1
    # le sous-groupe engendré par d est {0, g, 2g, ...} (g = gcd(d, m))
    for delta in range(0, m, g if d else m):
        h = (a0 ^ rotl(b0, delta, m)).bit_count()
        if h < best:
            best = h
        if best == 0:
            break
    if d == 0:  # pas identiques : delta reste 0 pour toujours
        best = (a0 ^ b0).bit_count()
    return best


def main() -> None:
    ap = build_argparser()
    a = ap.parse_args()
    params = params_from_args(a)
    sub = Substrate(params)
    sow(sub, params)

    quiet = 0
    for _ in range(a.ticks):
        st = sub.step()
        quiet = quiet + 1 if st.n_exec == 0 else 0
        if st.n_flight == 0:
            print("EXTINCTION : rien à certifier (flotte vide).")
            return
        if quiet >= 4 * params.m:
            break
    else:
        print(f"Pas de gel détecté en {a.ticks} ticks "
              f"(dernière activité récente) — certificat non applicable.")
        return

    print(f"Gel apparent au tick {sub.tick} "
          f"({len(sub.flight)} messagers, {len(sub.events) - 1} événements).")

    if params.k != 2:
        print("NOTE : le certificat n'est rigoureux que pour k=2 (pour k>2 "
              "il faudrait énumérer les groupes ; paires = condition "
              "nécessaire seulement).")

    buckets, membership = sub._locality()
    checked: set = set()
    n_pairs = 0
    n_sib = 0
    global_min = params.m + 1
    hist: dict[int, int] = {}
    worst_pair = None
    for aid in sorted(buckets):
        members = buckets[aid]
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                key = (members[i], members[j])
                if key in checked:
                    continue
                checked.add(key)
                ma, mb = sub.flight[key[0]], sub.flight[key[1]]
                if params.k == 2 and ma.emitter == mb.emitter:
                    # [A1] paire de même émetteur : ne peut jamais fournir
                    # deux causes distinctes -> ne peut jamais exécuter (k=2)
                    n_sib += 1
                    continue
                h = min_hamming_over_cycle(ma.state, ma.step,
                                           mb.state, mb.step, params.m)
                n_pairs += 1
                hist[h] = hist.get(h, 0) + 1
                if h < global_min:
                    global_min = h
                    worst_pair = key

    print(f"paires testables (A6) analysées : {n_pairs} "
          f"(+ {n_sib} paires de même émetteur, exclues par A1 pour k=2)")
    print("distribution du min de Hamming sur le cycle complet :")
    for h in sorted(hist):
        print(f"  minH={h:2d} : {hist[h]} paires")
    print(f"seuil s = {params.s} ; min global = {global_min} "
          f"(paire {worst_pair})")
    if global_min > params.s:
        print("CERTIFICAT : GEL ÉTERNEL PROUVÉ — aucune paire testable ne "
              "peut plus jamais satisfaire le prédicat A4, quel que soit le "
              "nombre de ticks futurs.")
    else:
        print("PAS de certificat : au moins une paire repassera sous le "
              "seuil ; le gel n'est qu'apparent (vérifier la fenêtre A6/"
              "consommation).")


if __name__ == "__main__":
    main()
