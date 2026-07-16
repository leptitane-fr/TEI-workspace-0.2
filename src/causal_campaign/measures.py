"""Instruments de mesure M1–M4 — côté EXPÉRIMENTATEUR uniquement.

Étanchéité (RÈGLE D'OR) : ce module consomme l'historique du réseau causal
produit par le moteur mais n'est JAMAIS importé par engine.py — aucune mesure
ne peut rétroagir sur la dynamique. Les flottants sont autorisés ici (le
substrat, lui, est entier). Les sources de BFS et tous les échantillonnages
sont DÉTERMINISTES (A8 s'applique aussi aux instruments, par hygiène).

Aucune fonction de ce module ne connaît de valeur cible : les estimateurs
publient des séries complètes (N(r), d(r), P(t), |I|(h)) — jamais une fenêtre
choisie a posteriori. La détection de plateau est agnostique de la valeur.
"""

from __future__ import annotations

import math
from collections import deque


# ---------------------------------------------------------------------------
# Utilitaires déterministes
# ---------------------------------------------------------------------------

def even_sources(nodes: list, n_sources: int = 10) -> list:
    """[M2][M3] Sources de BFS déterministes : indices régulièrement espacés dans la liste triée."""
    nodes = sorted(nodes)
    n = len(nodes)
    if n == 0:
        return []
    if n <= n_sources:
        return nodes
    return [nodes[(i * (n - 1)) // (n_sources - 1)] for i in range(n_sources)]


# ---------------------------------------------------------------------------
# M2 — Espace du front : graphe de proximité relationnelle + croissance N(r)
# ---------------------------------------------------------------------------

def front_proximity_graph(events: dict, front_eids: list, p: int) -> dict:
    """[M2] Graphe de proximité du front : deux événements récents sont voisins
    si leur ancêtre commun le plus récent est à profondeur <= p (même relation
    que la localité A6, recalculée ici depuis l'historique — instrument, pas règle).

    events : dict eid -> EventRecord ; front_eids : événements du front actif.
    Retourne dict eid -> set de voisins.
    """
    anc_of = {}
    for e in front_eids:
        seen = {e}
        frontier = [e]
        for _ in range(p):
            nxt = []
            for x in frontier:
                for par in events[x].parents:
                    if par not in seen:
                        seen.add(par)
                        nxt.append(par)
            frontier = nxt
        anc_of[e] = seen

    buckets: dict = {}
    for e in front_eids:
        for a in anc_of[e]:
            buckets.setdefault(a, []).append(e)

    adj: dict = {e: set() for e in front_eids}
    for a, members in buckets.items():
        if len(members) < 2:
            continue
        for i in range(len(members) - 1):
            for j in range(i + 1, len(members)):
                u, v = members[i], members[j]
                if u != v:
                    adj[u].add(v)
                    adj[v].add(u)
    return adj


def bfs_growth(adj: dict, sources: list) -> dict:
    """[M2] BFS multi-sources : N(r) moyen (volume de boule) et exposants locaux d(r).

    Publie la SÉRIE COMPLÈTE — aucune fenêtre choisie a posteriori.
    d(r) = dln N / dln r par différence centrée sur points intérieurs.
    """
    if not sources:
        return {"r": [], "N": [], "d_local": [], "per_source_N": [], "component_sizes": []}
    per_source = []
    comp_sizes = []
    for src in sources:
        dist = {src: 0}
        q = deque([src])
        counts = [1]
        while q:
            u = q.popleft()
            for v in adj.get(u, ()):
                if v not in dist:
                    dist[v] = dist[u] + 1
                    if dist[v] >= len(counts):
                        counts.append(0)
                    counts[dist[v]] += 1
                    q.append(v)
        cum = []
        tot = 0
        for c in counts:
            tot += c
            cum.append(tot)
        per_source.append(cum)
        comp_sizes.append(tot)

    rmax = max(len(c) for c in per_source)
    N = []
    for r in range(rmax):
        vals = [c[r] if r < len(c) else c[-1] for c in per_source]
        N.append(sum(vals) / len(vals))
    rs = list(range(rmax))
    d_local = [None]
    for r in range(1, rmax - 1):
        if N[r + 1] > 0 and N[r - 1] > 0 and r + 1 > 1 and r - 1 >= 1:
            d_local.append((math.log(N[r + 1]) - math.log(N[r - 1]))
                           / (math.log(r + 1) - math.log(r - 1)))
        else:
            d_local.append(None)
    if rmax > 1:
        d_local.append(None)
    return {"r": rs, "N": N, "d_local": d_local,
            "per_source_N": per_source, "component_sizes": comp_sizes}


# ---------------------------------------------------------------------------
# M3 — Dimension spectrale (probabilité de retour, marche paresseuse déterministe)
# ---------------------------------------------------------------------------

def spectral_return(adj: dict, sources: list, t_max: int = 128) -> dict:
    """[M3] P(t) ~ t^(-d_s/2) : probabilité de retour moyenne d'une marche
    paresseuse (P = 1/2 I + 1/2 D^-1 A), par itération de vecteurs — déterministe.

    Publie P(t) complet et d_s(t) = -2 dln P/dln t (pente centrée sur grille log).
    """
    if not sources:
        return {"t": [], "P": [], "d_s": []}
    nodes = sorted(adj)
    idx = {e: i for i, e in enumerate(nodes)}
    neigh = [[idx[v] for v in sorted(adj[e])] for e in nodes]
    deg = [max(1, len(nb)) for nb in neigh]

    P_series = [0.0] * (t_max + 1)
    for src in sources:
        v = [0.0] * len(nodes)
        v[idx[src]] = 1.0
        for t in range(1, t_max + 1):
            nv = [0.5 * x for x in v]
            for i, x in enumerate(v):
                if x != 0.0:
                    w = 0.5 * x / deg[i]
                    for j in neigh[i]:
                        nv[j] += w
            v = nv
            P_series[t] += v[idx[src]]
    ns = len(sources)
    P = [x / ns for x in P_series]

    ts = list(range(1, t_max + 1))
    d_s = []
    for t in ts:
        t2 = 2 * t
        if t2 <= t_max and P[t] > 0 and P[t2] > 0:
            d_s.append(-2.0 * (math.log(P[t2]) - math.log(P[t])) / (math.log(t2) - math.log(t)))
        else:
            d_s.append(None)
    return {"t": ts, "P": P[1:], "d_s": d_s}


# ---------------------------------------------------------------------------
# M1 — Dimension causale : scaling des intervalles + Myrheim-Meyer
# ---------------------------------------------------------------------------

def _ancestors_bounded(events: dict, q: int, min_depth: int) -> dict:
    """[M1] Ancêtres de q avec profondeur >= min_depth (BFS remontant, élagué)."""
    res = {q: events[q].depth}
    frontier = [q]
    while frontier:
        nxt = []
        for x in frontier:
            for par in events[x].parents:
                if par not in res and events[par].depth >= min_depth:
                    res[par] = events[par].depth
                    nxt.append(par)
        frontier = nxt
    return res


def causal_intervals(events: dict, children: dict, heights: list = None,
                     n_q: int = 12, mm_cap: int = 1500) -> dict:
    """[M1] |I(p,q)| ~ h^D et estimateur de Myrheim-Meyer.

    Échantillonnage déterministe : n_q événements q régulièrement espacés parmi
    les plus profonds ; pour chaque hauteur h, p = ancêtre d'identifiant minimal
    à profondeur depth(q)-h. Publie tous les couples (h, |I|) bruts, les pentes
    locales D(h) sur les moyennes log, et les estimations MM (fraction d'ordre).
    Si un espace-temps émerge : attendu D_causal ≈ d + 1.
    """
    if heights is None:
        heights = [3, 5, 8, 12, 17, 24, 34, 48]
    deep = sorted((e for e in events.values() if e.depth >= min(heights) + 1),
                  key=lambda e: (e.depth, e.eid))
    if not deep:
        return {"samples": [], "mean_logI_by_h": {}, "D_local": [], "mm": []}
    qs = [deep[(i * (len(deep) - 1)) // max(1, n_q - 1)].eid for i in range(min(n_q, len(deep)))]
    qs = sorted(set(qs))

    samples = []   # (q, p, h, |I|)
    mm = []        # (q, p, h, n, ordering_fraction, D_mm)
    for q in qs:
        dq = events[q].depth
        hs = [h for h in heights if h <= dq]
        if not hs:
            continue
        anc = _ancestors_bounded(events, q, dq - max(hs))
        by_depth: dict = {}
        for a, d in anc.items():
            if a != q and (d not in by_depth or a < by_depth[d]):
                by_depth[d] = a
        for h in hs:
            target = dq - h
            if target not in by_depth:
                continue
            pe = by_depth[target]
            interval = _interval(events, children, anc, pe, q)
            samples.append((q, pe, h, len(interval)))
            if 4 <= len(interval) <= mm_cap:
                r = _ordering_fraction(events, children, interval)
                mm.append((q, pe, h, len(interval), r, mm_dimension(r)))

    by_h: dict = {}
    for _, _, h, size in samples:
        by_h.setdefault(h, []).append(math.log(size))
    mean_log = {h: sum(v) / len(v) for h, v in by_h.items()}
    hs_sorted = sorted(mean_log)
    D_local = []
    for i in range(1, len(hs_sorted)):
        h0, h1 = hs_sorted[i - 1], hs_sorted[i]
        D_local.append((h1, (mean_log[h1] - mean_log[h0]) / (math.log(h1) - math.log(h0))))
    return {"samples": samples, "mean_logI_by_h": {str(h): mean_log[h] for h in hs_sorted},
            "D_local": D_local, "mm": mm}


def _interval(events: dict, children: dict, anc_q: dict, pe: int, q: int) -> list:
    """[M1] Intervalle causal I(p,q) = descendants(p) ∩ ancêtres(q), bornes incluses."""
    inside = {pe}
    frontier = [pe]
    while frontier:
        nxt = []
        for x in frontier:
            for c in children.get(x, ()):
                if c in anc_q and c not in inside:
                    inside.add(c)
                    nxt.append(c)
        frontier = nxt
    return sorted(inside)


def _ordering_fraction(events: dict, children: dict, interval: list) -> float:
    """[M1] Fraction de paires ordonnées 2R/(n(n-1)) dans l'intervalle (bitsets entiers)."""
    idx = {e: i for i, e in enumerate(interval)}
    inset = set(interval)
    order = sorted(interval, key=lambda e: -events[e].depth)
    reach = {}
    R = 0
    for e in order:
        mask = 0
        for c in children.get(e, ()):
            if c in inset:
                mask |= (1 << idx[c]) | reach.get(c, 0)
        reach[e] = mask
        R += mask.bit_count()
    n = len(interval)
    return 2.0 * R / (n * (n - 1)) if n > 1 else 0.0


def mm_ordering_fraction(d: float) -> float:
    """[M1] Fraction d'ordre attendue de Myrheim-Meyer en dimension d de Minkowski :
    r(d) = Γ(d+1)Γ(d/2) / (2Γ(3d/2)). Vérifié : r(2) = 1/2."""
    return math.exp(math.lgamma(d + 1) + math.lgamma(d / 2) - math.log(2) - math.lgamma(1.5 * d))


def mm_dimension(r: float) -> float:
    """[M1] Inverse numérique de mm_ordering_fraction (bissection ; r décroît avec d)."""
    if r >= mm_ordering_fraction(0.6):
        return 0.6
    if r <= mm_ordering_fraction(12.0):
        return 12.0
    lo, hi = 0.6, 12.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if mm_ordering_fraction(mid) > r:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


# ---------------------------------------------------------------------------
# M4 — Hauteur vs largeur (détection d'effondrement « 3 couches »)
# ---------------------------------------------------------------------------

def height_width(events: dict) -> dict:
    """[M4] Profil hauteur/largeur : nombre d'événements par couche de profondeur.

    Un effondrement type « 3 couches » = hauteur qui stagne pendant que la
    largeur explose (ratio largeur_max/hauteur divergent).
    """
    widths: dict = {}
    for e in events.values():
        widths[e.depth] = widths.get(e.depth, 0) + 1
    if not widths:
        return {"height": 0, "layer_widths": {}, "max_width": 0, "width_height_ratio": None}
    height = max(widths)
    max_w = max(widths.values())
    return {"height": height,
            "layer_widths": {str(d): widths[d] for d in sorted(widths)},
            "max_width": max_w,
            "width_height_ratio": (max_w / height) if height > 0 else None}


# ---------------------------------------------------------------------------
# Détection de plateau — agnostique de toute valeur cible (RÈGLE D'OR)
# ---------------------------------------------------------------------------

def plateau(xs: list, ys: list, tol: float = 0.10) -> dict:
    """Cherche la plus longue fenêtre [x_lo, x_hi] où la série y varie de < tol
    (max-min < tol * moyenne). Retourne la fenêtre, la valeur moyenne et le
    ratio x_hi/x_lo (>= 10 = une décade). NE compare à aucune cible : la
    comparaison aux critères pré-enregistrés n'a lieu que dans le rapport."""
    pts = [(x, y) for x, y in zip(xs, ys) if y is not None and x > 0]
    best = None
    n = len(pts)
    for i in range(n):
        for j in range(i + 1, n):
            window = [y for _, y in pts[i:j + 1]]
            mean = sum(window) / len(window)
            if mean == 0:
                continue
            if (max(window) - min(window)) < tol * abs(mean):
                span = pts[j][0] / pts[i][0]
                if best is None or span > best["span_ratio"]:
                    best = {"x_lo": pts[i][0], "x_hi": pts[j][0],
                            "value": mean, "span_ratio": span, "n_points": len(window)}
    return best or {"x_lo": None, "x_hi": None, "value": None, "span_ratio": 0.0, "n_points": 0}


def children_map(events: dict) -> dict:
    """[M1] Carte enfants (instrument) : eid -> liste des événements dont il est cause."""
    ch: dict = {}
    for e in events.values():
        for par in e.parents:
            ch.setdefault(par, []).append(e.eid)
    for v in ch.values():
        v.sort()
    return ch
