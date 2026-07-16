"""INSTRUMENTS DE MESURE M1–M5 — strictement en LECTURE SEULE.

ÉTANCHÉITÉ (RÈGLE D'OR) :
- ce module n'est JAMAIS importé par le substrat (vérifié par l'audit) ;
- il ne consomme que le journal brut des événements — des enregistrements
  plats (eid, parents, depth, tick) — et recalcule lui-même toute structure
  (ancêtres, adjacence) : aucune dépendance aux caches internes du substrat ;
- tout échantillonnage est DÉTERMINISTE (pas constant sur les identifiants),
  conformément à A8 étendu aux instruments ;
- la cible d ≈ 3 n'apparaît nulle part ici : les instruments publient des
  séries brutes (N(r), d(r), P(t), |I|(h)) ; la confrontation au critère
  pré-enregistré se fait dans le rapport.
"""

from __future__ import annotations

import math
from collections import deque

ROOT_ID = 0


class EventRec:
    """Enregistrement plat d'un événement (l'unique entrée des instruments)."""

    __slots__ = ("eid", "parents", "depth", "tick")

    def __init__(self, eid: int, parents: tuple, depth: int, tick: int) -> None:
        self.eid = eid
        self.parents = parents
        self.depth = depth
        self.tick = tick


def extract_log(substrate) -> list[EventRec]:
    """Copie plate du journal d'événements (ε inclus, filtré par les
    instruments). Ne lit que des attributs publics passifs."""
    return [EventRec(ev.eid, tuple(ev.parents), ev.depth, ev.tick)
            for ev in substrate.events]


# ----------------------------------------------------------------------
# Aides génériques
# ----------------------------------------------------------------------

def _parent_map(log: list[EventRec]) -> dict[int, tuple]:
    return {ev.eid: ev.parents for ev in log}


def _children_map(log: list[EventRec]) -> dict[int, list[int]]:
    ch: dict[int, list[int]] = {ev.eid: [] for ev in log}
    for ev in log:
        for pid in ev.parents:
            if pid in ch:
                ch[pid].append(ev.eid)
    return ch


def ancestors_within(eid: int, hops: int, pmap: dict[int, tuple]) -> set:
    """Ancêtres à <= hops sauts (soi inclus), recalculés depuis `parents`."""
    seen = {eid}
    frontier = [eid]
    for _ in range(hops):
        nxt = []
        for x in frontier:
            for pid in pmap.get(x, ()):
                if pid not in seen:
                    seen.add(pid)
                    nxt.append(pid)
        if not nxt:
            break
        frontier = nxt
    return seen


def loglog_fit(xs: list[float], ys: list[float]) -> tuple[float, float]:
    """Régression des moindres carrés sur (log x, log y) -> (pente, r²)."""
    pts = [(math.log(x), math.log(y)) for x, y in zip(xs, ys)
           if x > 0 and y > 0]
    n = len(pts)
    if n < 2:
        return float("nan"), float("nan")
    sx = sum(p[0] for p in pts)
    sy = sum(p[1] for p in pts)
    sxx = sum(p[0] * p[0] for p in pts)
    sxy = sum(p[0] * p[1] for p in pts)
    syy = sum(p[1] * p[1] for p in pts)
    den = n * sxx - sx * sx
    if den == 0:
        return float("nan"), float("nan")
    slope = (n * sxy - sx * sy) / den
    num_r = (n * sxy - sx * sy)
    den_r = math.sqrt(den * max(n * syy - sy * sy, 1e-30))
    r2 = (num_r / den_r) ** 2 if den_r > 0 else float("nan")
    return slope, r2


def local_exponents(xs: list[float], ys: list[float]) -> list[dict]:
    """Exposants locaux d(x) = dln(y)/dln(x) par différences centrées."""
    out = []
    for i in range(1, len(xs) - 1):
        if xs[i - 1] <= 0 or ys[i - 1] <= 0 or ys[i + 1] <= 0:
            continue
        dlx = math.log(xs[i + 1]) - math.log(xs[i - 1])
        dly = math.log(ys[i + 1]) - math.log(ys[i - 1])
        if dlx != 0:
            out.append({"x": xs[i], "exponent": dly / dlx})
    return out


# ----------------------------------------------------------------------
# M1 — Dimension causale : |I(p,q)| ~ h^D
# ----------------------------------------------------------------------

def m1_causal_intervals(log: list[EventRec], samples: int = 200,
                        h_max: int = 24) -> dict:
    """M1. Échantillonne des paires (p, q) avec q dans le futur de p (pas
    d'échantillonnage constant sur les eid, déterministe), mesure le volume
    de l'intervalle causal |I| = |desc(p) ∩ anc(q)| et la hauteur h (plus
    longue chaîne p→q). Publie la série brute et l'ajustement log-log."""
    core = [ev for ev in log if ev.eid != ROOT_ID]
    if len(core) < 10:
        return {"pairs": [], "D_causal": float("nan"), "r2": float("nan")}
    ch = _children_map(log)
    stride = max(1, len(core) // samples)
    pairs: list[dict] = []
    for idx in range(0, len(core), stride):
        src = core[idx]
        # Descendance bornée en hauteur (plus longue chaîne depuis src).
        height = {src.eid: 0}
        order = [src.eid]
        q = deque([src.eid])
        while q:
            x = q.popleft()
            hx = height[x]
            if hx >= h_max:
                continue
            for cid in ch.get(x, ()):
                nh = hx + 1
                if cid not in height or nh > height[cid]:
                    if cid not in height:
                        q.append(cid)
                        order.append(cid)
                    height[cid] = nh
        if len(order) < 3:
            continue
        # Un q par valeur de hauteur atteinte : le premier eid (déterministe).
        by_h: dict[int, int] = {}
        for eid in sorted(order):
            h = height[eid]
            if h >= 2 and h not in by_h:
                by_h[h] = eid
        desc = set(height)
        pmap_local = _parent_map(log)
        for h in sorted(by_h):
            qid = by_h[h]
            # anc(q) restreint à desc(p) : BFS arrière confinée.
            interval = {qid}
            bq = deque([qid])
            while bq:
                x = bq.popleft()
                for pid in pmap_local.get(x, ()):
                    if pid in desc and pid not in interval:
                        interval.add(pid)
                        bq.append(pid)
            if src.eid in interval:
                pairs.append({"h": h, "volume": len(interval)})
    if not pairs:
        return {"pairs": [], "D_causal": float("nan"), "r2": float("nan")}
    # Moyenne géométrique du volume par hauteur, puis ajustement.
    byh: dict[int, list[int]] = {}
    for pr in pairs:
        byh.setdefault(pr["h"], []).append(pr["volume"])
    hs = sorted(byh)
    vols = [math.exp(sum(math.log(v) for v in byh[h]) / len(byh[h]))
            for h in hs]
    slope, r2 = loglog_fit([float(h) for h in hs], vols)
    return {"pairs": pairs,
            "mean_volume_by_h": [{"h": h, "volume": v}
                                 for h, v in zip(hs, vols)],
            "local_D": local_exponents([float(h) for h in hs], vols),
            "D_causal": slope, "r2": r2}


# ----------------------------------------------------------------------
# M2 — Espace du front : N(r), d(r)
# ----------------------------------------------------------------------

def front_graph(log: list[EventRec], p: int, layers: int) -> dict[int, list[int]]:
    """Graphe de proximité du front : nœuds = événements des `layers`
    dernières couches ; arête ssi ancêtre commun à <= p sauts (la même
    relation que A6, utilisée ici comme INSTRUMENT, recalculée depuis
    `parents`). Retourne l'adjacence triée."""
    if not log:
        return {}
    dmax = max(ev.depth for ev in log)
    nodes = [ev for ev in log
             if ev.eid != ROOT_ID and ev.depth > dmax - layers]
    pmap = _parent_map(log)
    buckets: dict[int, list[int]] = {}
    for ev in sorted(nodes, key=lambda e: e.eid):
        for aid in sorted(ancestors_within(ev.eid, p, pmap)):
            buckets.setdefault(aid, []).append(ev.eid)
    adj: dict[int, set] = {ev.eid: set() for ev in nodes}
    for aid in sorted(buckets):
        members = buckets[aid]
        if len(members) < 2:
            continue
        for a in members:
            adj[a].update(members)
    return {eid: sorted(s - {eid}) for eid, s in sorted(adj.items())}


def m2_front_growth(adj: dict[int, list[int]], sources: int = 64) -> dict:
    """M2. BFS multi-sources (échantillonnage par pas constant) sur le graphe
    du front : publie N(r) moyen (taille cumulée de boule) et la série
    complète des exposants locaux d(r)."""
    ids = sorted(adj)
    if len(ids) < 4:
        return {"N_r": [], "d_r": [], "n_nodes": len(ids)}
    stride = max(1, len(ids) // sources)
    picked = ids[::stride]
    balls: list[list[int]] = []   # une liste cumulée N_s(r) par source
    for s in picked:
        dist = {s: 0}
        q = deque([s])
        while q:
            x = q.popleft()
            for y in adj[x]:
                if y not in dist:
                    dist[y] = dist[x] + 1
                    q.append(y)
        if len(dist) < 4:
            continue
        rmax = max(dist.values())
        hist = [0] * (rmax + 1)
        for d in dist.values():
            hist[d] += 1
        cum_list = []
        cum = 0
        for c in hist:
            cum += c
            cum_list.append(cum)
        balls.append(cum_list)
    count_src = len(balls)
    if count_src == 0:
        return {"N_r": [], "d_r": [], "n_nodes": len(ids)}
    # Une boule épuisée reste à sa taille finale (saturation) : on prolonge
    # chaque N_s(r) à r_max global avant de moyenner, sinon la moyenne
    # chuterait artificiellement quand les petites composantes sortent.
    rmax_all = max(len(b) - 1 for b in balls)
    n_r = [{"r": r,
            "N": sum(b[r] if r < len(b) else b[-1] for b in balls) / count_src}
           for r in range(rmax_all + 1)]
    d_r = local_exponents([float(e["r"]) for e in n_r if e["r"] > 0],
                          [e["N"] for e in n_r if e["r"] > 0])
    return {"N_r": n_r,
            "d_r": [{"r": e["x"], "d": e["exponent"]} for e in d_r],
            "n_nodes": len(ids), "n_sources": count_src,
            "r_max": rmax_all}


# ----------------------------------------------------------------------
# M3 — Dimension spectrale : P(t) ~ t^(-d_s/2)
# ----------------------------------------------------------------------

def m3_spectral(adj: dict[int, list[int]], sources: int = 32,
                t_max: int = 256) -> dict:
    """M3. Marche paresseuse (1/2 rester, 1/2 voisin uniforme) itérée en
    exact (vecteurs de probabilité, aucun tirage). P(t) = probabilité de
    retour moyenne sur les sources ; d_s(t) = -2 dlnP/dlnt."""
    ids = [i for i in sorted(adj) if adj[i]]
    if len(ids) < 4:
        return {"P_t": [], "d_s": []}
    stride = max(1, len(ids) // sources)
    picked = ids[::stride]
    p_t: list[float] = []
    vecs = {s: {s: 1.0} for s in picked}
    for t in range(1, t_max + 1):
        ret = 0.0
        for s in picked:
            v = vecs[s]
            nv: dict[int, float] = {}
            for x, px in v.items():
                nv[x] = nv.get(x, 0.0) + 0.5 * px
                deg = len(adj[x])
                if deg:
                    share = 0.5 * px / deg
                    for y in adj[x]:
                        nv[y] = nv.get(y, 0.0) + share
            # Élagage numérique (instrument) : les masses < 1e-12 sont
            # négligées pour borner le coût ; sans effet au-delà du bruit.
            vecs[s] = {x: q for x, q in nv.items() if q > 1e-12}
            ret += vecs[s].get(s, 0.0)
        p_t.append(ret / len(picked))
    ts = [float(t) for t in range(1, t_max + 1)]
    loc = local_exponents(ts, p_t)
    return {"P_t": [{"t": int(t), "P": p} for t, p in zip(ts, p_t)],
            "d_s": [{"t": e["x"], "d_s": -2.0 * e["exponent"]} for e in loc],
            "n_sources": len(picked)}


# ----------------------------------------------------------------------
# M4 — Hauteur vs largeur
# ----------------------------------------------------------------------

def m4_height_width(log: list[EventRec]) -> dict:
    """M4. Profil des couches du réseau causal : hauteur (profondeur max),
    largeur par couche, largeur max/moyenne."""
    widths: dict[int, int] = {}
    for ev in log:
        if ev.eid == ROOT_ID:
            continue
        widths[ev.depth] = widths.get(ev.depth, 0) + 1
    if not widths:
        return {"height": 0, "widths": [], "width_max": 0, "width_mean": 0.0}
    height = max(widths)
    series = [{"depth": d, "width": widths[d]} for d in sorted(widths)]
    vals = list(widths.values())
    return {"height": height, "widths": series,
            "width_max": max(vals),
            "width_mean": sum(vals) / len(vals)}


# ----------------------------------------------------------------------
# Checkpoint complet (M1–M4 ; M5 = série de checkpoints, assemblée en aval)
# ----------------------------------------------------------------------

def full_checkpoint(log: list[EventRec], p: int, cfg) -> dict:
    """Toutes les mesures sur l'état courant de l'historique. `cfg` est une
    ExperimenterConfig (tailles d'échantillonnage des instruments)."""
    adj = front_graph(log, p, cfg.front_layers)
    return {
        "m1": m1_causal_intervals(log, cfg.m1_samples),
        "m2": m2_front_growth(adj, cfg.m2_sources),
        "m3": m3_spectral(adj, cfg.m3_sources, cfg.m3_tmax),
        "m4": m4_height_width(log),
    }
