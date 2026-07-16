"""Tests de conformité axiomatique — exécutables avec `python3 -m pytest` ou directement.

Ces tests vérifient les propriétés STRUCTURELLES exigées par l'axiomatique,
jamais une valeur de mesure (RÈGLE D'OR : aucun test ne connaît de cible).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from causal_campaign.engine import Engine, Messenger, rotl, birth_rot, _OSC_RULES  # noqa: E402
from causal_campaign.params import Params  # noqa: E402
from causal_campaign.seeds import build_engine, SEEDS  # noqa: E402

SRC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "causal_campaign")


def _run_hash(params: Params, ticks: int, max_events: int = 2000) -> tuple:
    """Empreinte complète d'un run : flux d'événements + états finaux des messagers.

    Caps de ressources de test (la dynamique peut exploser — A9) : arrêt
    d'observation au-delà de max_events, jamais de bridage de la dynamique.
    """
    eng = build_engine(params)
    for _ in range(ticks):
        eng.step()
        eng.apply_window(params.W)
        if not eng.flight or eng.aborted or len(eng.events) > max_events:
            break
    ev = tuple((e.eid, e.parents, e.depth, e.tick) for e in eng.events)
    fl = tuple((m.mid, m.state) for m in eng.flight)
    return ev, fl


def test_a8_determinisme_integral():
    """[A8] Deux exécutions de la même configuration produisent un flux identique."""
    p = Params(max_ticks=200, max_candidate_pairs_per_tick=300_000)
    assert _run_hash(p, 200) == _run_hash(p, 200)


def test_a8_aucun_prng():
    """[A8] Aucun module du substrat n'importe de source aléatoire."""
    for fname in os.listdir(SRC_DIR):
        if not fname.endswith(".py"):
            continue
        with open(os.path.join(SRC_DIR, fname), encoding="utf-8") as fh:
            text = fh.read()
        for forbidden in ("import random", "from random", "import secrets", "os.urandom",
                          "numpy.random", "time.time()"):
            assert forbidden not in text, f"{fname} contient '{forbidden}'"


def test_a3_oscillation_inversible_periode_finie():
    """[A3] Chaque règle d'oscillation est une bijection de période finie."""
    m = 32
    for rule_name, rule in _OSC_RULES.items():
        st0 = 0xDEADBEEF & ((1 << m) - 1)
        msg = Messenger(0, st0, birth_rot(st0, m), 0, 0, (frozenset([0]),), frozenset([0]))
        seen = {}
        for t in range(4 * m * m):
            if msg.state in seen:
                break
            seen[msg.state] = t
            msg.state = rule(msg, m)
        assert msg.state in seen, f"{rule_name}: pas de cycle détecté"
        assert seen[msg.state] == 0, f"{rule_name}: pré-période non nulle => non inversible"


def test_a1_deux_causes_minimum():
    """[A1] Tout événement dynamique a >= 2 causes distinctes ; orientation acyclique par profondeur."""
    for seed in SEEDS:
        p = Params(seed_name=seed, max_ticks=300, max_candidate_pairs_per_tick=300_000)
        eng = build_engine(p)
        n_seed = len(eng.events)
        for _ in range(300):
            eng.step()
            eng.apply_window(p.W)
            if not eng.flight or eng.aborted or len(eng.events) > 2000:
                break
        by_id = {e.eid: e for e in eng.events}
        for e in eng.events[n_seed:]:
            assert len(set(e.parents)) >= 2, f"événement {e.eid}: moins de 2 causes"
            for par in e.parents:
                assert by_id[par].depth < e.depth, "orientation passé->futur violée"


def test_a5_relais_sans_memoire_de_trajet():
    """[A5] Le messager ne transporte ni compteur de distance ni trajet (slots audités)."""
    allowed = {"mid", "state", "rot", "emit_eid", "emit_depth", "anc_levels", "roots"}
    assert set(Messenger.__slots__) == allowed


def test_etancheite_generation_mesure():
    """[RÈGLE D'OR] Le moteur n'importe jamais les instruments de mesure."""
    for fname in ("engine.py", "seeds.py", "params.py"):
        with open(os.path.join(SRC_DIR, fname), encoding="utf-8") as fh:
            text = fh.read()
        for forbidden in ("measures", "runner", "journal", "sweep"):
            assert f"import {forbidden}" not in text and f"from .{forbidden}" not in text, \
                f"{fname} importe {forbidden} : étanchéité violée"


def test_a12_engine_sans_flottants():
    """[A12] Le substrat est entier : aucune arithmétique flottante dans engine.py."""
    import ast
    with open(os.path.join(SRC_DIR, "engine.py"), encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError(f"float {node.value} ligne {node.lineno} dans engine.py")


def test_rotl_inversible():
    """[A3] rotl est inversible : rotl(rotl(x, r), m-r) == x."""
    m = 32
    for x in (0, 1, 0xFFFFFFFF, 0xA5A5A5A5, 0x12345678):
        for r in (1, 5, 17, 31):
            assert rotl(rotl(x, r, m), m - r, m) == x & ((1 << m) - 1)


def test_a13_photon_bijectif_preserve_information():
    """[A13] L'émission photonique est une bijection de F2^m (non destructive)."""
    from causal_campaign.engine import photon_emission
    for m in (16, 32, 64):
        seen = set()
        for x in range(0, 1 << 16, 257):  # échantillon déterministe
            y = photon_emission(x & ((1 << m) - 1), m)
            assert y not in seen
            seen.add(y)
        # inversibilité explicite : rot puis xor => xor puis rot inverse
        mask = (1 << m) - 1
        r = (m // 2) | 1
        for x in (0, 1, 0xBEEF & mask, mask):
            y = photon_emission(x, m)
            assert rotl(y ^ (0x504F4C41524954E5 & mask), m - r, m) == x


def test_a13_cmax_zero_identique_a1_a12():
    """[A13] C_max=0 désactive strictement A13 : aucune trajectoire modifiée."""
    p0 = Params(max_ticks=150, max_candidate_pairs_per_tick=300_000)
    p1 = Params(max_ticks=150, max_candidate_pairs_per_tick=300_000, C_max=0)
    assert _run_hash(p0, 150) == _run_hash(p1, 150)


def test_a13_determinisme_et_a1_sur_soupe():
    """[A8][A13] Déterminisme intégral et >= 2 causes sur un germe soupe avec saturation."""
    p = Params(seed_name="soup_diluted", f=3, k=2, s=8, C_max=1,
               max_ticks=40, max_candidate_pairs_per_tick=600_000)
    assert _run_hash(p, 40, max_events=4000) == _run_hash(p, 40, max_events=4000)
    eng = build_engine(p)
    n_seed = len(eng.events)
    assert n_seed >= 500, "soupe primordiale : >= 500 événements initiaux"
    for _ in range(30):
        eng.step()
        eng.apply_window(p.W)
        if eng.aborted or len(eng.events) > 5000:
            break
    by_id = {e.eid: e for e in eng.events}
    for e in eng.events[n_seed:]:
        assert len(set(e.parents)) >= 2
        for par in e.parents:
            assert by_id[par].depth < e.depth


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"OK  {fn.__name__}")
    print(f"\n{len(fns)} tests passés.")
