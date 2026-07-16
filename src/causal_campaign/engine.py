"""Moteur du substrat — réseau causal de messagers (axiomes A1–A12).

Chaque fonction porte l'annotation de l'axiome qu'elle implémente.
Le moteur est INTÉGRALEMENT ENTIER et DÉTERMINISTE (A8) : aucun float,
aucun PRNG, aucune statistique globale dans les règles (A6/A12).

Étanchéité génération/mesure : le moteur ne consulte JAMAIS l'historique
du réseau (A7). Chaque messager transporte localement les identifiants
de ses ancêtres à profondeur <= p ; c'est la seule information relationnelle
utilisée par la dynamique. L'historique complet des événements est produit
en sortie pour l'expérimentateur (mesures), jamais relu par le moteur.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .params import Params

# ---------------------------------------------------------------------------
# Primitives déterministes (A8) — hachage entier et rotations.
# ---------------------------------------------------------------------------

_MASK64 = (1 << 64) - 1
_GOLD = 0x9E3779B97F4A7C15  # ratio doré 64 bits (constante de hachage classique)


def mix64(x: int) -> int:
    """[A8] Finaliseur splitmix64 : hachage entier déterministe, sans PRNG.

    Toute la « diversité » du système provient de cette fonction appliquée
    aux états internes — jamais d'une source aléatoire.
    """
    x &= _MASK64
    x ^= x >> 30
    x = (x * 0xBF58476D1CE4E5B9) & _MASK64
    x ^= x >> 27
    x = (x * 0x94D049BB133111EB) & _MASK64
    x ^= x >> 31
    return x


def rotl(x: int, r: int, m: int) -> int:
    """[A3] Rotation de bits à gauche sur m bits — opération inversible de période finie."""
    r %= m
    mask = (1 << m) - 1
    return ((x << r) | (x >> (m - r))) & mask


# ---------------------------------------------------------------------------
# Structures du substrat
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EventRecord:
    """[A1] Événement du réseau causal (enregistrement pour l'expérimentateur).

    parents : tuple trié d'identifiants d'événements causes (>= 2 pour tout
    événement dynamique ; vide uniquement pour les racines du germe, qui sont
    des données initiales déclarées, pas des produits de la dynamique).
    """

    eid: int
    parents: tuple
    depth: int
    tick: int


class Messenger:
    """[A2][A5] Messager porteur d'état : mot de m bits + rotation propre.

    anc_levels : tuple de frozensets — anc_levels[d] = identifiants des
    ancêtres de l'événement d'émission situés exactement à profondeur d
    (d = 0 est l'événement d'émission lui-même). C'est le SEUL bagage
    relationnel du messager (A6) : pas de coordonnées, pas de compteur de
    distance, pas d'information de trajet (A5).
    roots : frozenset des racines ancêtres (utilisé UNIQUEMENT par le
    contrôle négatif M7-ii « p = infini » ; jamais par la dynamique nominale).
    """

    __slots__ = ("mid", "state", "rot", "emit_eid", "emit_depth", "anc_levels", "roots")

    def __init__(self, mid: int, state: int, rot: int, emit_eid: int,
                 emit_depth: int, anc_levels: tuple, roots: frozenset):
        self.mid = mid
        self.state = state
        self.rot = rot
        self.emit_eid = emit_eid
        self.emit_depth = emit_depth
        self.anc_levels = anc_levels
        self.roots = roots


@dataclass
class TickReport:
    """Sortie d'observation d'un tick (expérimentateur) — aucune rétroaction possible."""

    tick: int
    new_events: list          # list[EventRecord]
    n_flight: int
    n_candidate_pairs: int
    n_executed: int
    n_windowed_out: int


# ---------------------------------------------------------------------------
# Règles d'oscillation (A3) — degré de liberté déclaré
# ---------------------------------------------------------------------------


def _osc_rot_birth(msg: Messenger, m: int) -> int:
    """[A3] Oscillation « rot_birth » : rotation de pas fixe propre au messager.

    Le pas (msg.rot) est dérivé déterministiquement de l'état de naissance ;
    rotation => inversible, période finie divisant m / gcd(rot, m).
    Les périodes varient librement d'un messager à l'autre (A10).
    """
    return rotl(msg.state, msg.rot, m)


def _osc_rot1_xor(msg: Messenger, m: int) -> int:
    """[A3] Oscillation « rot1_xor » : rotation d'un bit puis XOR d'une clé de naissance.

    Application affine inversible sur F2^m => période finie. La clé propre
    (msg.rot, réinterprété comme clé m bits via mix64) diversifie les périodes.
    """
    mask = (1 << m) - 1
    key = mix64(msg.rot * _GOLD) & mask
    return rotl(msg.state, 1, m) ^ key


_OSC_RULES = {"rot_birth": _osc_rot_birth, "rot1_xor": _osc_rot1_xor}


# ---------------------------------------------------------------------------
# Prédicats de compatibilité (A4) — degré de liberté déclaré
# ---------------------------------------------------------------------------


def _pred_hamming(a: int, b: int, s: int, m: int) -> bool:
    """[A4] Prédicat « hamming » : distance de Hamming(a, b) <= s. Local, rare si s << m/2."""
    return (a ^ b).bit_count() <= s


def _pred_block_zero(a: int, b: int, s: int, m: int) -> bool:
    """[A4] Prédicat « block_zero » : au moins s blocs de 8 bits du XOR sont nuls.

    Famille structurellement différente de Hamming (coïncidence par motifs
    de blocs plutôt que par bits individuels).
    """
    x = a ^ b
    zero_blocks = 0
    for _ in range(m // 8):
        if (x & 0xFF) == 0:
            zero_blocks += 1
        x >>= 8
    return zero_blocks >= s


_PREDICATES = {"hamming": _pred_hamming, "block_zero": _pred_block_zero}


# ---------------------------------------------------------------------------
# Règles de composition d'état (A2) — degré de liberté déclaré
# ---------------------------------------------------------------------------


def _compose_fold_rot_xor(states: tuple, m: int) -> int:
    """[A2] Composition « fold_rot_xor » : repli XOR-rotation-hachage des états parents.

    Fonction déterministe des états des messagers exécutés (ordre canonique
    fourni par l'appelant). Résultat = graine 64 bits pour la portée émise.
    """
    c = _GOLD
    for i, st in enumerate(states):
        c = mix64(c ^ rotl(st, (7 * i + 1) % m, m) ^ ((i + 1) * 0xD1B54A32D192ED03 & _MASK64))
    return c


def _compose_fold_mul_add(states: tuple, m: int) -> int:
    """[A2] Composition « fold_mul_add » : repli multiplicatif (famille distincte)."""
    c = 0xC2B2AE3D27D4EB4F
    for st in states:
        c = mix64((c * 0x100000001B3 + st) & _MASK64)
    return c


_COMPOSE_RULES = {"fold_rot_xor": _compose_fold_rot_xor, "fold_mul_add": _compose_fold_mul_add}


def child_state(compose_seed: int, branch: int, m: int) -> int:
    """[A2] État du messager n° branch émis par un événement (fonction déterministe de la graine composée)."""
    return mix64(compose_seed + (branch + 1) * _GOLD) & ((1 << m) - 1)


def birth_rot(state: int, m: int) -> int:
    """[A3] Pas de rotation propre du messager, dérivé de son état de naissance (déterministe, A8).

    1 <= rot <= m-1 : jamais la rotation nulle, donc oscillation effective.
    """
    return 1 + (mix64(state ^ 0xA24BAED4963EE407) % (m - 1))


# ---------------------------------------------------------------------------
# Moteur
# ---------------------------------------------------------------------------


class Engine:
    """[A1–A12] Moteur synchrone du réseau causal.

    A10 : un pas de relais par tick pour tout messager en vol (le moteur
    synchrone implémente le tick de relais, pas une horloge de calcul) ;
    les périodes internes (A3) varient librement par messager.
    A9 : aucune conservation — le vol croît ou s'éteint selon les exécutions.
    """

    def __init__(self, params: Params):
        params.validate()
        self.P = params
        self.tick = 0
        self.next_eid = 0
        self.next_mid = 0
        self.max_depth = 0
        self.flight: list[Messenger] = []      # messagers en vol (état du tick courant, A7)
        self.newborn: list[Messenger] = []     # émis ce tick, éligibles au tick suivant
        self.events: list[EventRecord] = []    # HISTORIQUE — instrument d'expérimentateur uniquement (A7)
        self._osc = _OSC_RULES[params.osc_rule]
        self._pred = _PREDICATES[params.predicate]
        self._compose = _COMPOSE_RULES[params.compose_rule]
        self.aborted: Optional[str] = None
        self._seed_anc: dict = {}
        self._seed_roots: dict = {}

    # ------------------------------------------------------------------
    # Germe (données initiales déclarées — A8 : états par formule explicite)
    # ------------------------------------------------------------------

    def add_seed_event(self, parents: tuple, states: list) -> int:
        """[A8] Ajoute un événement de germe avec des états de messagers donnés par formule.

        Les racines (parents=()) sont des données initiales ; un événement de
        germe non racine doit avoir >= 2 causes (A1). Aucune géométrie : le
        germe ne fournit que des identifiants et des mots de bits.
        """
        assert len(parents) == 0 or len(parents) >= 2, "A1 : tout événement non racine a >= 2 causes"
        eid = self.next_eid
        self.next_eid += 1
        if parents:
            pdepth = max(self.events[pe].depth for pe in parents)
            depth = pdepth + 1
            levels = self._child_anc_levels([self._seed_anc[pe] for pe in parents], eid)
            roots = frozenset().union(*(self._seed_roots[pe] for pe in parents))
        else:
            depth = 0
            levels = tuple([frozenset([eid])] + [frozenset()] * self.P.p)
            roots = frozenset([eid])
        self._seed_anc[eid] = levels
        self._seed_roots[eid] = roots
        rec = EventRecord(eid=eid, parents=tuple(sorted(parents)), depth=depth, tick=0)
        self.events.append(rec)
        self.max_depth = max(self.max_depth, depth)
        for j, st in enumerate(states):
            st &= (1 << self.P.m) - 1
            self.flight.append(Messenger(self.next_mid, st, birth_rot(st, self.P.m),
                                         eid, depth, levels, roots))
            self.next_mid += 1
        return eid

    # ------------------------------------------------------------------
    # Boucle de tick
    # ------------------------------------------------------------------

    def step(self) -> TickReport:
        """[A10] Un tick de relais universel : oscillation (A3) puis exécution conditionnelle (A4)."""
        self.tick += 1
        P = self.P

        # -- A3 : oscillation discrète de tout messager en vol --
        osc, m = self._osc, P.m
        for msg in self.flight:
            msg.state = osc(msg, m)

        # -- A4 + A6 : appariement local rare --
        pairs, n_candidates = self._candidate_compatible_pairs()
        if n_candidates > P.max_candidate_pairs_per_tick:
            # Truncature de ressources d'expérimentateur : on ARRÊTE l'observation,
            # on ne bride jamais la dynamique (A9/A12).
            self.aborted = "candidate_explosion"
            return TickReport(self.tick, [], len(self.flight), n_candidates, 0, 0)

        executed_sets = self._greedy_match(pairs)

        # -- A1 + A2 : création d'événements et émission de messagers --
        new_events = [self._execute(group) for group in executed_sets]

        # Les messagers exécutés quittent le vol ; les autres continuent (A5).
        consumed = set()
        for group in executed_sets:
            for msg in group:
                consumed.add(msg.mid)
        if consumed:
            self.flight = [msg for msg in self.flight if msg.mid not in consumed]

        # Les nouveaux-nés rejoignent le vol, éligibles à partir du tick suivant.
        self.flight.extend(self.newborn)
        self.newborn = []

        return TickReport(self.tick, new_events, len(self.flight),
                          n_candidates, len(executed_sets), 0)

    def apply_window(self, W: int) -> int:
        """[A11] Truncature d'expérimentateur : retire du domaine simulé les messagers
        dont l'événement d'émission est à profondeur > W derrière le front actif.

        Ce n'est PAS une règle du substrat — W est balayé (M6) pour vérifier
        l'indépendance des résultats. Retourne le nombre de messagers retirés.
        """
        cut = self.max_depth - W
        if cut <= 0:
            return 0
        before = len(self.flight)
        self.flight = [msg for msg in self.flight if msg.emit_depth >= cut]
        return before - len(self.flight)

    # ------------------------------------------------------------------
    # Appariement (A4, A6) et contrôles négatifs (M7)
    # ------------------------------------------------------------------

    def _candidate_compatible_pairs(self):
        """[A6] Génère les paires candidates par localité relationnelle puis filtre par le prédicat (A4).

        Nominal : deux messagers ne sont testés que si leurs événements
        d'émission partagent un ancêtre à profondeur <= p (seaux par ancêtre).
        Aucune coordonnée, aucun mélange global, aucune statistique globale.

        M7-ii (control_p_infinite) : ancêtre commun à profondeur quelconque
        (équivalent prouvable : intersection des ensembles de racines non vide).
        M7-iii (control_ignore_causality) : toute paire est testée, la
        structure causale est ignorée par la dynamique.
        Retourne (liste triée de paires compatibles, nb de paires candidates testées).
        """
        P = self.P
        flight = self.flight
        pred, s, m = self._pred, P.s, P.m
        trivial = P.control_trivial_predicate  # [M7-i] compatibilité toujours vraie

        # Construction des seaux de candidats
        buckets: dict = {}
        if P.control_ignore_causality:
            buckets[0] = list(range(len(flight)))
        elif P.control_p_infinite:
            # racine partagée <=> ancêtre commun à profondeur quelconque
            for i, msg in enumerate(flight):
                for r in msg.roots:
                    buckets.setdefault(r, []).append(i)
        else:
            for i, msg in enumerate(flight):
                for level in msg.anc_levels:
                    for a in level:
                        buckets.setdefault(a, []).append(i)

        seen = set()
        compatible = []
        n_candidates = 0
        cap = P.max_candidate_pairs_per_tick
        for key in sorted(buckets):
            idxs = buckets[key]
            if len(idxs) < 2:
                continue
            for u in range(len(idxs) - 1):
                i = idxs[u]
                mi = flight[i]
                for v in range(u + 1, len(idxs)):
                    j = idxs[v]
                    pk = (i, j) if i < j else (j, i)
                    if pk in seen:
                        continue
                    seen.add(pk)
                    n_candidates += 1
                    if n_candidates > cap:
                        return [], n_candidates
                    mj = flight[j]
                    if trivial or pred(mi.state, mj.state, s, m):
                        compatible.append((flight[pk[0]].mid, flight[pk[1]].mid, pk[0], pk[1]))
        # Ordre canonique global (A8 : déterminisme intégral de l'appariement)
        compatible.sort()
        return compatible, n_candidates

    def _greedy_match(self, pairs) -> list:
        """[A4][A8] Appariement glouton déterministe en k-groupes mutuellement compatibles.

        Parcours des paires compatibles en ordre canonique (mid croissants) ;
        un groupe est accepté s'il atteint la taille k avec >= 2 événements
        d'émission distincts (A1 : >= 2 causes). k = 2 : appariement simple.
        """
        P = self.P
        flight = self.flight
        if P.k == 2:
            used = set()
            groups = []
            for _, _, i, j in pairs:
                a, b = flight[i], flight[j]
                if a.mid in used or b.mid in used:
                    continue
                if a.emit_eid == b.emit_eid:
                    continue  # A1 : deux causes distinctes exigées
                used.add(a.mid)
                used.add(b.mid)
                groups.append((a, b))
            return groups

        # k >= 3 : cliques gloutonnes sur le graphe de compatibilité
        adj: dict = {}
        for _, _, i, j in pairs:
            adj.setdefault(i, set()).add(j)
            adj.setdefault(j, set()).add(i)
        used_idx = set()
        groups = []
        for i in sorted(adj):
            if i in used_idx:
                continue
            clique = [i]
            for j in sorted(adj[i]):
                if j in used_idx or j in clique:
                    continue
                if all(j in adj.get(c, ()) for c in clique):
                    clique.append(j)
                    if len(clique) == P.k:
                        break
            if len(clique) == P.k:
                members = [flight[c] for c in clique]
                if len({msg.emit_eid for msg in members}) >= 2:  # A1
                    used_idx.update(clique)
                    groups.append(tuple(members))
        return groups

    def _child_anc_levels(self, parent_levels: list, eid: int) -> tuple:
        """[A6] Ancêtres à profondeur <= p du nouvel événement, calculés localement.

        levels[d] du fils = union des levels[d-1] des parents ; levels[0] = {fils}.
        Information strictement locale transportée par les messagers (A7).
        """
        p = self.P.p
        levels = [frozenset([eid])]
        for d in range(1, p + 1):
            acc = set()
            for pl in parent_levels:
                acc |= pl[d - 1]
            levels.append(frozenset(acc))
        return tuple(levels)

    def _execute(self, group: tuple) -> EventRecord:
        """[A1][A2] Exécution : k messagers compatibles créent un événement qui émet f messagers.

        - parents = événements d'émission distincts des messagers exécutés (>= 2, A1)
        - états émis = fonction déterministe des états exécutés (A2, ordre canonique)
        - aucune conservation imposée : f et k sont indépendants (A9)
        """
        P = self.P
        eid = self.next_eid
        self.next_eid += 1
        # Ordre canonique des entrées (A8)
        members = sorted(group, key=lambda msg: (msg.emit_eid, msg.mid))
        parents = tuple(sorted({msg.emit_eid for msg in members}))
        depth = 1 + max(msg.emit_depth for msg in members)
        rec = EventRecord(eid=eid, parents=parents, depth=depth, tick=self.tick)
        self.events.append(rec)
        if depth > self.max_depth:
            self.max_depth = depth

        # Ancêtres locaux <= p : union par événement parent distinct
        by_parent = {}
        for msg in members:
            by_parent[msg.emit_eid] = msg.anc_levels
        levels = self._child_anc_levels(list(by_parent.values()), eid)
        roots = frozenset().union(*(msg.roots for msg in members))

        seed = self._compose(tuple(msg.state for msg in members), P.m)
        for j in range(P.f):
            st = child_state(seed, j, P.m)
            self.newborn.append(Messenger(self.next_mid, st, birth_rot(st, P.m),
                                          eid, depth, levels, roots))
            self.next_mid += 1
        return rec
