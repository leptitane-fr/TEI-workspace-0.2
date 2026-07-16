"""Tests de conformité axiomatique et d'étanchéité.

Exécuter : python3 -m unittest tests.test_axioms -v
"""

import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "src"))

from causalnet.params import ExperimenterConfig, Params  # noqa: E402
from causalnet.seeds import sow  # noqa: E402
from causalnet.substrate import Substrate, rotl  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_ticks(params: Params, n: int) -> Substrate:
    sub = Substrate(params)
    sow(sub, params)
    for _ in range(n):
        st = sub.step()
        if st.n_flight == 0:
            break
    return sub


def log_signature(sub: Substrate) -> tuple:
    events = tuple((ev.eid, ev.parents, ev.depth, ev.tick)
                   for ev in sub.events)
    flight = tuple((m.mid, m.state, m.step, m.emitter)
                   for _, m in sorted(sub.flight.items()))
    return events, flight


class TestA3Oscillation(unittest.TestCase):
    def test_rotation_inversible(self):
        """A3 : la rotation est inversible (rotl puis rotl inverse = id)."""
        m = 32
        for x in [0, 1, 0xDEADBEEF & 0xFFFFFFFF, (1 << m) - 1]:
            for r in [1, 5, 17, 31]:
                self.assertEqual(rotl(rotl(x, r, m), m - r, m), x)

    def test_periode_finie(self):
        """A3 : période interne finie (au plus m rotations reviennent)."""
        m = 32
        x0 = 0x12345678
        x = x0
        for _ in range(m):
            x = rotl(x, 3, m)
        # gcd(3,32)=1 : période exactement m
        self.assertEqual(x, x0)


class TestA8Determinisme(unittest.TestCase):
    def test_deux_runs_identiques(self):
        """A8 : deux exécutions aux mêmes paramètres donnent des historiques
        strictement identiques (événements ET messagers en vol)."""
        params = Params(seed_N=500)
        sig1 = log_signature(run_ticks(params, 15))
        sig2 = log_signature(run_ticks(params, 15))
        self.assertEqual(sig1, sig2)

    def test_zero_prng(self):
        """A8 : aucun module random/secrets importé dans src/."""
        src = os.path.join(ROOT, "src", "causalnet")
        for fname in os.listdir(src):
            if fname.endswith(".py"):
                with open(os.path.join(src, fname), encoding="utf-8") as fh:
                    text = fh.read()
                self.assertNotIn("import random", text, fname)
                self.assertNotIn("import secrets", text, fname)


class TestA1Causalite(unittest.TestCase):
    def test_dag_et_deux_causes(self):
        """A1 : tout événement créé par la dynamique a >= 2 causes, toutes
        antérieures (DAG, orientation passé -> futur)."""
        params = Params(seed_N=500)
        sub = run_ticks(params, 20)
        n_dyn = 0
        for ev in sub.events:
            if ev.eid == 0 or ev.parents == (0,):
                continue  # ε et germe
            n_dyn += 1
            self.assertGreaterEqual(len(ev.parents), 2)
            for pid in ev.parents:
                self.assertLess(pid, ev.eid)  # cause strictement antérieure
        self.assertGreater(n_dyn, 0, "aucune exécution en 20 ticks : "
                                     "test non probant")


class TestA5A7NonMemoire(unittest.TestCase):
    def test_messager_sans_trajet(self):
        """A5 : le messager ne stocke que (état, pas propre, émetteur) —
        aucun compteur de distance, aucune information de trajet."""
        from causalnet.substrate import Messenger
        self.assertEqual(set(Messenger.__slots__),
                         {"mid", "state", "step", "emitter"})


class TestA11Troncature(unittest.TestCase):
    def test_fenetre_respectee(self):
        """A11 : aucun messager en vol n'a un émetteur à plus de W couches
        derrière le front."""
        params = Params(seed_N=500, W=4)
        sub = run_ticks(params, 30)
        for msg in sub.flight.values():
            depth = sub._event_by_id[msg.emitter].depth
            self.assertGreaterEqual(depth, sub.front_depth - params.W)


class TestEtancheite(unittest.TestCase):
    def test_audit_statique(self):
        """Règle d'or : l'audit statique complet doit passer."""
        proc = subprocess.run(
            [sys.executable, os.path.join(ROOT, "scripts",
                                          "audit_etancheite.py")],
            capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0,
                         f"audit en échec :\n{proc.stdout}\n{proc.stderr}")


class TestGermes(unittest.TestCase):
    def test_taille_imposee(self):
        """Le germe massif est obligatoire (500 <= N <= 1000)."""
        p = Params(seed_N=100)  # constructible, mais semis interdit
        sub = Substrate(p)
        with self.assertRaises(ValueError):
            sow(sub, p)

    def test_reproductibilite_formule(self):
        """A8 : le germe est une formule fermée — deux semis identiques."""
        p = Params(seed_N=500)
        s1, s2 = Substrate(p), Substrate(p)
        sow(s1, p)
        sow(s2, p)
        self.assertEqual(log_signature(s1), log_signature(s2))


if __name__ == "__main__":
    unittest.main()
