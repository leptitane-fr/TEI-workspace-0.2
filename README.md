# Campagne : émergence d'une dimension de croissance d ≈ 3 dans une classe de réseaux causaux

Recherche exploratoire sur une classe précise de dynamiques de réseaux causaux
(axiomatique fermée A1–A13, voir `AXIOMES.md`). Objectif d'**observation** (et
uniquement d'observation) : déterminer si cette classe peut produire un régime
spatial émergent de dimension de croissance d ≈ 3, stable et stationnaire.
Verdict exigé : **OUI** / **NON** / **INDÉTERMINÉ** — voir `rapport/VERDICT.md`.

## Règle d'or (anti-ajustement)

La cible d ≈ 3 n'existe **que** dans les instruments de mesure et le critère de
succès pré-enregistré (`PROTOCOLE.md`). Elle n'entre **jamais** dans le système
de règles :

- le substrat (`src/causalnet/substrate.py`, `src/causalnet/seeds.py`) est
  aveugle à toute grandeur macroscopique — aucune dimension, aucun exposant,
  aucun diamètre cible, aucune correction asservie à une mesure ;
- génération et mesure sont 100 % étanches : le substrat n'importe aucun module
  de mesure (vérifié statiquement par `scripts/audit_etancheite.py` et
  `tests/test_axioms.py`) ;
- chaque fonction du substrat est annotée de l'axiome qu'elle implémente
  (`[A1]`…`[A13]`) ; tout mécanisme sans provenance axiomatique = violation =
  run invalide ;
- l'itération sur les règles est permise uniquement pour la conformité
  axiomatique et l'obtention d'un régime physique stationnaire, jamais pour
  forcer un exposant.

## Arborescence

```
AXIOMES.md                  Axiomatique A1–A13 + interprétation opérationnelle déclarée
PROTOCOLE.md                Mesures M1–M7, critère de succès pré-enregistré, règles de campagne
src/causalnet/
  params.py                 Degrés de liberté légitimes (et rien d'autre)
  substrate.py              La dynamique — étanche, annotée axiome par axiome
  seeds.py                  Soupe primordiale (formule explicite, zéro géométrie)
  controls.py               M7 — contrôles négatifs (substrats volontairement cassés)
  measure.py                M1–M5 — instruments (lecture seule de l'historique)
  journal.py                Journalisation exhaustive de TOUS les runs (y compris ratés)
scripts/
  run_single.py             Un run instrumenté complet
  run_sweep.py              M6 — balayage des paramètres libres (dont W)
  run_controls.py           M7 — les trois contrôles négatifs
  smoke_test.py             Test de bout en bout rapide
  audit_etancheite.py       Audit statique de la règle d'or
tests/test_axioms.py        Tests de conformité (déterminisme A8, inversibilité A3, étanchéité)
journal/RUNLOG.md           Journal de campagne (append-only)
data/                       Données brutes par run : N(r), d(r), P(t), |I|(h), tables
rapport/VERDICT.md          Rapport de verdict (trois branches exclusives)
```

## Utilisation

Aucune dépendance externe (Python ≥ 3.10, stdlib uniquement).

```bash
python3 scripts/audit_etancheite.py        # audit règle d'or (doit passer avant tout run)
python3 -m unittest tests.test_axioms -v   # conformité axiomatique
python3 scripts/smoke_test.py              # chaîne complète sur un petit run
python3 scripts/run_single.py --ticks 400  # run instrumenté (paramètres par défaut)
python3 scripts/run_sweep.py               # campagne M6
python3 scripts/run_controls.py            # campagne M7
```

Chaque run écrit `data/runs/<run_id>/` (params, séries brutes, résultat JSON)
et ajoute une ligne au `journal/RUNLOG.md`. Les runs avortés (explosion,
extinction, dépassement de ressources) sont journalisés comme les autres :
ce sont des résultats (A9).
