"""M7 — CONTRÔLES NÉGATIFS.

Trois substrats VOLONTAIREMENT CASSÉS, chacun retirant un pilier de
l'axiomatique. Ce ne sont PAS des dynamiques candidates : ils n'existent que
comme instruments de falsification (chacun doit dégrader ou casser le régime,
sinon le régime n'était pas porté par l'axiome retiré).

Chaque contrôle est étiqueté et journalisé comme tel ; aucun résultat de
contrôle n'entre dans le verdict autrement que par M7.
"""

from __future__ import annotations

from .params import Params
from .substrate import Substrate, Messenger, mix64


class ControlTrivialCompat(Substrate):
    """M7(i) — compatibilité TRIVIALE : le prédicat A4 accepte tout couple.

    (Équivalent à s = m ; la rareté exigée par A4 est supprimée.)
    """

    CONTROL_NAME = "M7i_compat_triviale"

    def _compatible(self, a: Messenger, b: Messenger) -> bool:  # override A4
        return True


class ControlNoLocality(Substrate):
    """M7(ii) — localité RETIRÉE (p = infini) : tout messager est testable
    avec tout autre, mélange global — négation directe de A6."""

    CONTROL_NAME = "M7ii_sans_localite"

    def _locality(self):  # override A6 : godet global unique
        ids = sorted(self.flight)
        return {0: ids}, {mid: [0] for mid in ids}


class ControlAcausal(Substrate):
    """M7(iii) — causalité IGNORÉE : les causes du nouvel événement ne sont
    plus les événements d'émission des messagers exécutés, mais deux
    événements passés choisis par brouillage déterministe de l'identifiant —
    la cohérence causale (A1) est détruite, le graphe reste un DAG mais ses
    liens ne transportent plus l'information des rencontres."""

    CONTROL_NAME = "M7iii_causalite_ignoree"

    def step(self):
        # Détourne la parenté APRÈS coup : on laisse la dynamique tourner,
        # mais chaque événement créé pendant ce tick voit ses causes
        # re-câblées vers des événements passés arbitraires (hash de l'eid).
        n_before = len(self.events)
        stats = super().step()
        pool = n_before  # événements disponibles comme causes (indices < pool)
        for ev in self.events[n_before:]:
            if pool < 3:
                break
            a = 1 + (mix64(ev.eid * 2 + 1) % (pool - 1))
            b = 1 + (mix64(ev.eid * 2 + 2) % (pool - 1))
            if a == b:
                b = 1 + (b % (pool - 1))
            ev.parents = tuple(sorted({self.events[a].eid,
                                       self.events[b].eid}))
            # NB : depth et anc restent ceux de la création ; la mesure M1/M2
            # lit `parents`, c'est la structure causale publiée qui est cassée.
        return stats


def make_control(name: str, params: Params) -> Substrate:
    table = {
        ControlTrivialCompat.CONTROL_NAME: ControlTrivialCompat,
        ControlNoLocality.CONTROL_NAME: ControlNoLocality,
        ControlAcausal.CONTROL_NAME: ControlAcausal,
    }
    return table[name](params)


ALL_CONTROLS = [ControlTrivialCompat.CONTROL_NAME,
                ControlNoLocality.CONTROL_NAME,
                ControlAcausal.CONTROL_NAME]
