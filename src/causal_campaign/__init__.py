"""causal_campaign — campagne exploratoire sur les dynamiques de réseaux causaux.

Étanchéité stricte génération/mesure :
  - engine.py, seeds.py, params.py : le SUBSTRAT (A1–A12, entier, déterministe)
  - measures.py, runner.py, journal.py, sweep.py : l'EXPÉRIMENTATEUR (M1–M7)
engine.py n'importe jamais les modules de mesure — vérifié par tests/test_axioms.py.
"""

from .params import Params
from .engine import Engine
from .seeds import build_engine, SEEDS

__all__ = ["Params", "Engine", "build_engine", "SEEDS"]
