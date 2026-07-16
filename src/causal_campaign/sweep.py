"""Orchestration de campagne — M6 (robustesse) et M7 (contrôles négatifs).

Côté expérimentateur. Le critère d'itération sur les règles est la conformité
axiomatique et l'existence d'un régime stationnaire (M5), JAMAIS la valeur
d'un exposant (RÈGLE D'OR). Ce module ne contient aucune valeur cible.
"""

from __future__ import annotations

from dataclasses import replace

from .params import Params
from .runner import run, summarize
from .seeds import CAMPAIGN_SEEDS


def run_seed_battery(base: Params, label_prefix: str, verbose: bool = True,
                     seeds: tuple = CAMPAIGN_SEEDS) -> list:
    """[M6] Les >= 3 germes obligatoires, même configuration par ailleurs."""
    results = []
    for seed in seeds:
        params = replace(base, seed_name=seed)
        res = run(params, f"{label_prefix}-seed_{seed}", note=f"battery germes ({seed})")
        if verbose:
            print(summarize(res))
        results.append(res)
    return results


def run_param_sweep(base: Params, param_name: str, values: list,
                    label_prefix: str, verbose: bool = True) -> list:
    """[M6] Balayage d'UN paramètre libre (plateau vs curseur).

    Publie un run complet par valeur — la question posée : le régime est-il un
    attracteur d'une région étendue, ou un point réglé ? Inclut le balayage de
    W (A11 : aucun résultat ne doit dépendre de la fenêtre).
    """
    results = []
    for v in values:
        params = replace(base, **{param_name: v})
        res = run(params, f"{label_prefix}-{param_name}_{v}", note=f"sweep {param_name}={v}")
        if verbose:
            print(summarize(res))
        results.append(res)
    return results


def run_negative_controls(base: Params, label_prefix: str, verbose: bool = True) -> list:
    """[M7] Les trois contrôles négatifs pré-enregistrés.

    Chacun DOIT dégrader ou casser le régime nominal, sinon l'ingrédient
    correspondant ne fait rien — à dire dans le rapport.
      (i)   compatibilité triviale (toujours vraie)
      (ii)  localité retirée (p = infini)
      (iii) causalité ignorée dans la dynamique
    """
    controls = [
        ("ctrl_trivial", {"control_trivial_predicate": True}),
        ("ctrl_p_inf", {"control_p_infinite": True}),
        ("ctrl_no_causality", {"control_ignore_causality": True}),
    ]
    results = []
    for name, flags in controls:
        params = replace(base, **flags)
        res = run(params, f"{label_prefix}-{name}", note=f"contrôle négatif {name}")
        if verbose:
            print(summarize(res))
        results.append(res)
    return results
