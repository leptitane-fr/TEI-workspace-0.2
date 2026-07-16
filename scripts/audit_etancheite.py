#!/usr/bin/env python3
"""AUDIT STATIQUE DE LA RÈGLE D'OR — à exécuter avant toute campagne.

Vérifie sur les SOURCES du substrat (substrate.py, seeds.py, params.py) :
1. qu'aucun module de mesure n'y est importé (étanchéité génération/mesure) ;
2. qu'aucun vocabulaire de grandeur macroscopique cible n'y apparaît
   (dimension, exposant, diamètre, plateau, cible...) hors docstrings de
   conformité ;
3. qu'aucun module `random`/`secrets`/`numpy.random` n'est importé où que ce
   soit dans src/ (A8) ;
4. que chaque fonction/méthode du substrat porte au moins une annotation
   d'axiome [A1]..[A13] dans sa docstring (provenance axiomatique).

Sortie non nulle = violation = campagne interdite.
"""

import ast
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src", "causalnet")

SUBSTRATE_FILES = ["substrate.py", "seeds.py", "params.py"]
FORBIDDEN_IMPORTS_SUBSTRATE = {"measure", "causalnet.measure", "journal",
                               "causalnet.journal", "runner",
                               "causalnet.runner"}
FORBIDDEN_IMPORTS_ALL = {"random", "secrets", "numpy.random"}
# Vocabulaire de pilotage macroscopique interdit dans le CODE du substrat
# (identifiants et commentaires de logique ; les mentions du présent audit
# et des docstrings d'étanchéité sont autorisées via la liste blanche).
FORBIDDEN_TOKENS = [
    r"\bdimension\b", r"\bexposant\b", r"\bexponent\b", r"\bdiamet",
    r"\btarget\b", r"\bcible\b", r"\bfractal", r"\bspectral",
]
TOKEN_WHITELIST_LINES = ("RÈGLE D'OR", "grandeur macroscopique",
                         "AUCUNE", "aveugle")

AXIOM_RE = re.compile(r"\[A(1[0-3]|[1-9])\]")
# Fonctions utilitaires/structurelles exemptées d'annotation d'axiome
# (allocation d'identifiants, enregistrement passif, sortie d'observation).
EXEMPT_FUNCS = {"__init__", "__post_init__", "to_dict", "snapshot",
                "_alloc_eid", "_alloc_mid", "_register_event",
                "_anc_levels_root"}


def fail(msgs: list[str]) -> None:
    print("AUDIT ÉTANCHÉITÉ : ÉCHEC")
    for m in msgs:
        print("  -", m)
    sys.exit(1)


def main() -> None:
    problems: list[str] = []

    for fname in sorted(os.listdir(SRC)):
        if not fname.endswith(".py"):
            continue
        path = os.path.join(SRC, fname)
        with open(path, encoding="utf-8") as fh:
            source = fh.read()
        tree = ast.parse(source, filename=fname)

        # (1) + (3) imports
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                names = [mod] + [f"{mod}.{a.name}" if mod else a.name
                                 for a in node.names]
            for name in names:
                short = name.split(".")[-1]
                if name in FORBIDDEN_IMPORTS_ALL or short in {"random",
                                                              "secrets"}:
                    problems.append(f"{fname}: import interdit (A8) : {name}")
                if fname in SUBSTRATE_FILES and (
                        name in FORBIDDEN_IMPORTS_SUBSTRATE
                        or short in {"measure", "journal", "runner"}):
                    problems.append(
                        f"{fname}: le substrat importe un instrument : {name}")

        if fname in SUBSTRATE_FILES:
            # (2) vocabulaire macroscopique dans le code du substrat
            for i, line in enumerate(source.splitlines(), 1):
                if any(w in line for w in TOKEN_WHITELIST_LINES):
                    continue
                for pat in FORBIDDEN_TOKENS:
                    if re.search(pat, line, flags=re.IGNORECASE):
                        problems.append(
                            f"{fname}:{i}: vocabulaire macroscopique "
                            f"interdit dans le substrat : {line.strip()!r}")
            # (4) provenance axiomatique de chaque fonction
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name in EXEMPT_FUNCS:
                        continue
                    doc = ast.get_docstring(node) or ""
                    if not AXIOM_RE.search(doc):
                        problems.append(
                            f"{fname}:{node.lineno}: fonction sans "
                            f"provenance axiomatique : {node.name}")

    if problems:
        fail(problems)
    print("AUDIT ÉTANCHÉITÉ : OK (substrat aveugle, imports propres, "
          "provenance axiomatique complète)")


if __name__ == "__main__":
    main()
