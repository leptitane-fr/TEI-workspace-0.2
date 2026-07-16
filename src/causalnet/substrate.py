"""SUBSTRAT DYNAMIQUE — implémentation stricte de l'axiomatique A1–A13.

ÉTANCHÉITÉ (RÈGLE D'OR) :
- ce module n'importe AUCUN instrument de mesure et ne calcule AUCUNE
  grandeur macroscopique (dimension, exposant, diamètre, ...) ;
- aucune règle n'est asservie à une mesure : toutes sont locales et
  myopes [A12] ;
- zéro générateur pseudo-aléatoire [A8] : toute diversité provient des états
  internes et de fonctions déterministes explicites ;
- chaque fonction porte l'annotation de l'axiome qu'elle implémente.

L'historique (liste d'événements) est append-only : il n'est JAMAIS relu par
les règles [A7], il n'existe que comme enregistrement pour les instruments.
"""

from __future__ import annotations

from typing import Optional

from .params import Params

# Identifiant du nœud formel ε (origine causale de la soupe primordiale).
# Cf. AXIOMES.md, interprétation opérationnelle n°1 : ε n'émet rien, ne porte
# aucun état, et sort de toutes les fenêtres de parenté dès que le front
# dépasse la profondeur p.
ROOT_ID = 0

_U64 = 0xFFFFFFFFFFFFFFFF


def mix64(x: int) -> int:
    """[A8] Finaliseur SplitMix64 : fonction de brouillage DÉTERMINISTE.

    Formule algébrique explicite et fixe — ce n'est pas un générateur (aucun
    état interne, aucune graine cachée) ; utilisée pour dériver des mots à
    partir d'entiers de manière reproductible.
    """
    x &= _U64
    x = ((x ^ (x >> 30)) * 0xBF58476D1CE4E5B9) & _U64
    x = ((x ^ (x >> 27)) * 0x94D049BB133111EB) & _U64
    return (x ^ (x >> 31)) & _U64


def mix_m(x: int, m: int) -> int:
    """[A8] Brouillage déterministe réduit à un mot de m bits."""
    return mix64(x) & ((1 << m) - 1)


def rotl(x: int, r: int, m: int) -> int:
    """[A3] Rotation de bits à gauche sur m bits — opération INVERSIBLE."""
    r %= m
    mask = (1 << m) - 1
    return ((x << r) | (x >> (m - r))) & mask


def hamming(a: int, b: int) -> int:
    """[A4] Distance de Hamming entre deux mots d'état."""
    return (a ^ b).bit_count()


class Event:
    """[A1] Événement du réseau causal.

    parents : tuple trié d'identifiants d'événements antérieurs (>= 2 causes
    pour tout événement créé par la dynamique ; le germe est la condition
    initiale, rattachée au nœud formel ε).
    depth   : 1 + max(profondeur des causes) — orientation passé→futur
              structurelle.
    anc     : anc[j] = frozenset des ancêtres à <= j sauts (soi inclus),
              j = 0..p. Structure RELATIONNELLE statique figée à la naissance,
              support de la localité [A6] ; aucune coordonnée, aucun
              plongement.
    """

    __slots__ = ("eid", "parents", "depth", "tick", "anc")

    def __init__(self, eid: int, parents: tuple, depth: int, tick: int,
                 anc: tuple) -> None:
        self.eid = eid
        self.parents = parents
        self.depth = depth
        self.tick = tick
        self.anc = anc


class Messenger:
    """[A2] Messager porteur d'état.

    state   : mot de m bits (état interne composé).
    step    : pas de rotation propre, dérivé déterministiquement de l'état de
              naissance [A3][A10] — les périodes internes varient librement.
    emitter : identifiant de l'événement d'émission (support de [A6]).
    Conformément à [A5] : AUCUN compteur de distance, AUCUNE information de
    trajet n'est stockée.
    """

    __slots__ = ("mid", "state", "step", "emitter")

    def __init__(self, mid: int, state: int, step: int, emitter: int) -> None:
        self.mid = mid
        self.state = state
        self.step = step
        self.emitter = emitter


class TickStats:
    """Compte-rendu passif d'un tick (sortie d'observation, pas une entrée de
    règle [A7][A12])."""

    __slots__ = ("tick", "n_exec", "n_flight", "n_events", "front_depth",
                 "n_truncated")

    def __init__(self, tick: int, n_exec: int, n_flight: int, n_events: int,
                 front_depth: int, n_truncated: int) -> None:
        self.tick = tick
        self.n_exec = n_exec
        self.n_flight = n_flight
        self.n_events = n_events
        self.front_depth = front_depth
        self.n_truncated = n_truncated

    def to_dict(self) -> dict:
        return {"tick": self.tick, "n_exec": self.n_exec,
                "n_flight": self.n_flight, "n_events": self.n_events,
                "front_depth": self.front_depth,
                "n_truncated": self.n_truncated}


class Substrate:
    """La dynamique complète A1–A13. Aveugle à toute grandeur macroscopique."""

    def __init__(self, params: Params) -> None:
        self.P = params
        self.tick = 0
        self.events: list[Event] = []          # historique append-only [A7]
        self._event_by_id: dict[int, Event] = {}
        self.flight: dict[int, Messenger] = {}  # messagers en vol (id -> M)
        self._next_eid = 0
        self._next_mid = 0
        self.front_depth = 0
        # ε : origine causale formelle de l'hypersurface initiale
        # (AXIOMES.md, interprétation n°1).
        root = Event(self._alloc_eid(), (), 0, 0,
                     self._anc_levels_root(params.p))
        self._register_event(root)

    # ------------------------------------------------------------------
    # Allocation & structures relationnelles
    # ------------------------------------------------------------------

    def _alloc_eid(self) -> int:
        eid = self._next_eid
        self._next_eid += 1
        return eid

    def _alloc_mid(self) -> int:
        mid = self._next_mid
        self._next_mid += 1
        return mid

    @staticmethod
    def _anc_levels_root(p: int) -> tuple:
        base = frozenset((ROOT_ID,))
        return tuple(base for _ in range(p + 1))

    def _anc_levels(self, eid: int, parents: tuple) -> tuple:
        """[A6] Calcule anc[0..p] : ancêtres à <= j sauts (soi inclus).

        Purement relationnel : union des niveaux j-1 des causes. Aucune
        coordonnée, aucun mélange global.
        """
        p = self.P.p
        levels = [frozenset((eid,))]
        for j in range(1, p + 1):
            acc = {eid}
            for pid in parents:
                acc.update(self._event_by_id[pid].anc[j - 1])
            levels.append(frozenset(acc))
        return tuple(levels)

    def _register_event(self, ev: Event) -> None:
        self.events.append(ev)
        self._event_by_id[ev.eid] = ev
        if ev.depth > self.front_depth:
            self.front_depth = ev.depth

    # ------------------------------------------------------------------
    # Émission
    # ------------------------------------------------------------------

    def add_seed_event(self, tick: int) -> Event:
        """[A1] Événement du germe : condition initiale, cause unique ε.

        (Le germe n'est pas un « nouvel événement » de la dynamique — la
        contrainte des deux causes de [A1] s'applique aux événements créés
        par exécution ; cf. AXIOMES.md, interprétation n°1.)
        """
        eid = self._alloc_eid()
        parents = (ROOT_ID,)
        ev = Event(eid, parents, 1, tick, self._anc_levels(eid, parents))
        self._register_event(ev)
        return ev

    def emit(self, state: int, emitter_eid: int) -> Messenger:
        """[A2][A3] Met en vol un messager ; son pas de rotation propre est
        dérivé déterministiquement de son état de naissance."""
        m = self.P.m
        step = 1 + (mix64(state ^ 0xC0FFEE_0DD) % (m - 1))
        msg = Messenger(self._alloc_mid(), state & ((1 << m) - 1), step,
                        emitter_eid)
        self.flight[msg.mid] = msg
        return msg

    # ------------------------------------------------------------------
    # Règles élémentaires (chacune : un axiome)
    # ------------------------------------------------------------------

    def _oscillate_all(self) -> None:
        """[A3][A10] Un pas de relais universel et synchrone : chaque messager
        en vol subit sa rotation propre (inversible, période finie)."""
        m = self.P.m
        if self.P.rot_rule == "rotl_step":
            for msg in self.flight.values():
                msg.state = rotl(msg.state, msg.step, m)
        elif self.P.rot_rule == "rotl_1":
            for msg in self.flight.values():
                msg.state = rotl(msg.state, 1, m)
        else:
            raise ValueError(f"rot_rule inconnue : {self.P.rot_rule}")

    def _buckets(self) -> dict[int, list[int]]:
        """[A6] Godets de localité relationnelle : ancêtre -> messagers dont
        l'événement d'émission contient cet ancêtre à profondeur <= p. Deux
        messagers ne sont testables que s'ils partagent un godet."""
        buckets: dict[int, list[int]] = {}
        for mid in sorted(self.flight):            # ordre déterministe [A8]
            emitter = self._event_by_id[self.flight[mid].emitter]
            for aid in sorted(emitter.anc[self.P.p]):
                buckets.setdefault(aid, []).append(mid)
        return buckets

    def _neighborhoods(self, buckets: dict[int, list[int]]) -> dict[int, list[int]]:
        """[A6][A13] Pour chaque messager : la liste triée des messagers
        testables avec lui (candidats A4) ; sa taille est la densité locale
        qui alimente le déphasage thermique A13."""
        neigh: dict[int, set] = {mid: set() for mid in self.flight}
        for aid in sorted(buckets):
            members = buckets[aid]
            if len(members) < 2:
                continue
            mset = set(members)
            for mid in members:
                neigh[mid].update(mset)
        return {mid: sorted(s - {mid}) for mid, s in neigh.items()}

    def _compatible(self, a: Messenger, b: Messenger) -> bool:
        """[A4] Prédicat de compatibilité local sur les états (rare : s << m).
        Ne consulte QUE les états du tick courant [A7]."""
        if self.P.predicate_rule == "hamming_pivot":
            return hamming(a.state, b.state) <= self.P.s
        raise ValueError(f"predicate_rule inconnue : {self.P.predicate_rule}")

    def _compose_states(self, states: list[int]) -> int:
        """[A2] Composition déterministe des états des messagers qui ont
        produit l'événement (repli XOR + rotations + multiplicateur impair)."""
        m = self.P.m
        mask = (1 << m) - 1
        if self.P.compose_rule == "fold_xor_rot":
            acc = 0
            for st in states:
                acc = rotl(acc, 5, m) ^ st
                acc = (acc * 0x9E3779B1) & mask
            return acc
        if self.P.compose_rule == "fold_add_rot":
            acc = 0
            for st in states:
                acc = (rotl(acc, 3, m) + st) & mask
                acc ^= (acc >> 7)
            return acc & mask
        raise ValueError(f"compose_rule inconnue : {self.P.compose_rule}")

    def _dephase(self, state: int, density: int, j: int) -> int:
        """[A13] Déphasage thermique : masque XOR dont le poids (nombre de
        bits) est STRICTEMENT PROPORTIONNEL à la densité locale de messagers
        en vol (saturation uniquement à m, taille physique du mot). Aucun
        seuil, aucun quota, aucune exécution empêchée [A9].
        """
        m = self.P.m
        nbits = min(m, (density * self.P.dephase_num) // self.P.dephase_den)
        if nbits <= 0:
            return state
        pos = mix64(state ^ mix64(0xD3_0000 + j)) % m
        mask = rotl((1 << nbits) - 1, pos, m)
        return state ^ mask

    # ------------------------------------------------------------------
    # Le tick
    # ------------------------------------------------------------------

    def step(self) -> TickStats:
        """Un tick complet : oscillation [A3][A10], appariement local
        [A4][A6], exécutions [A1][A2][A13], troncature déclarée [A11].

        Aucune conservation imposée [A9] : le nombre d'exécutions par tick
        n'est ni plafonné ni encouragé.
        """
        self.tick += 1
        self._oscillate_all()

        buckets = self._buckets()
        neigh = self._neighborhoods(buckets)

        # --- Appariement glouton déterministe [A4][A8] ---
        consumed: set = set()
        executions: list[tuple[list[int], int]] = []  # (mids, densité pivot)
        k = self.P.k
        for pivot_mid in sorted(self.flight):
            if pivot_mid in consumed:
                continue
            pivot = self.flight[pivot_mid]
            group = [pivot_mid]
            emitters = {pivot.emitter}
            for cand_mid in neigh[pivot_mid]:
                if cand_mid in consumed or cand_mid == pivot_mid:
                    continue
                cand = self.flight[cand_mid]
                if not self._compatible(pivot, cand):
                    continue
                if len(group) == k - 1 and len(emitters) < 2 \
                        and cand.emitter in emitters:
                    # [A1] dernier siège réservé à une seconde cause distincte
                    continue
                group.append(cand_mid)
                emitters.add(cand.emitter)
                if len(group) == k:
                    break
            if len(group) == k and len(emitters) >= 2:   # [A1] >= 2 causes
                consumed.update(group)
                executions.append((group, len(neigh[pivot_mid])))

        # --- Exécutions : nouveaux événements + émissions [A1][A2][A13] ---
        for group, density in executions:
            msgs = [self.flight[mid] for mid in group]
            parents = tuple(sorted({mg.emitter for mg in msgs}))
            depth = 1 + max(self._event_by_id[pid].depth for pid in parents)
            eid = self._alloc_eid()
            ev = Event(eid, parents, depth, self.tick,
                       self._anc_levels(eid, parents))
            self._register_event(ev)
            base = self._compose_states([mg.state for mg in msgs])
            for j in range(self.P.f):                       # [A2] fan-out f
                child = mix_m(base ^ mix64(0xE9_0000 + j), self.P.m)
                child = self._dephase(child, density, j)    # [A13]
                self.emit(child, eid)
            for mid in group:                # consommation (AXIOMES.md n°2)
                del self.flight[mid]

        # --- [A5] les messagers non exécutés continuent, sans rien stocker ---

        # --- [A11] Troncature d'expérimentateur, déclarée ---
        n_trunc = 0
        limit = self.front_depth - self.P.W
        if limit > 0:
            stale = [mid for mid in sorted(self.flight)
                     if self._event_by_id[self.flight[mid].emitter].depth < limit]
            for mid in stale:
                del self.flight[mid]
            n_trunc = len(stale)

        return TickStats(self.tick, len(executions), len(self.flight),
                         len(self.events) - 1,  # ε exclu du compte
                         self.front_depth, n_trunc)

    # ------------------------------------------------------------------
    # État agrégé (lecture seule, pour instruments et journal)
    # ------------------------------------------------------------------

    def snapshot(self) -> dict:
        return {"tick": self.tick, "n_flight": len(self.flight),
                "n_events": len(self.events) - 1,
                "front_depth": self.front_depth}
