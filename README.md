# Campagne exploratoire — dimension de croissance des réseaux causaux

Recherche exploratoire sur une classe de dynamiques de réseaux causaux (axiomatique fermée
A1–A12) avec une cible explicite : déterminer si cette classe peut produire un régime
spatial émergent de **dimension de croissance d ≈ 3, stable et stationnaire** — et livrer un
verdict tranché (OUI / NON / INDÉTERMINÉ). Voir `PROTOCOL.md` (pré-enregistrement complet)
et `AUDIT.md` (provenance axiomatique de chaque mécanisme).

## Principe anti-ajustement (RÈGLE D'OR)

La cible est connue de l'expérimentateur mais n'entre **jamais** dans le système. Le code de
génération (substrat) et le code de mesure (instruments) sont étanches — vérifié par test.
L'itération sur les règles n'est permise que sur critère de conformité axiomatique et de
stabilité, jamais sur la valeur d'un exposant.

## Arborescence

```
PROTOCOL.md              Pré-enregistrement : axiomes, mesures, critères de succès, verdict
AUDIT.md                 Table fonction → axiome + points d'audit sensibles
src/causal_campaign/
  params.py              Degrés de liberté légitimes + caps de ressources
  engine.py              SUBSTRAT : moteur A1–A12 (entier, déterministe, myope)
  seeds.py               Germes pauvres (vee, wedge4, braid6 + témoin antichain2)
  measures.py            INSTRUMENTS : M1 (dim. causale), M2 (front N(r), d(r)),
                         M3 (dim. spectrale), M4 (hauteur/largeur), plateau agnostique
  runner.py              Boucle d'observation, séries par tick (M5), checkpoints
  journal.py             Journal exhaustif append-only (tous les runs, y compris ratés)
  sweep.py               M6 (batterie germes, balayages) et M7 (contrôles négatifs)
scripts/
  run_single.py          Un run : python3 scripts/run_single.py s=14 f=2 seed_name=vee
  pilot.py               Campagne pilote (validation bout-en-bout, petites tailles)
  campaign.py            Campagne complète par étages (1..5)
tests/test_axioms.py     Conformité axiomatique mécanique (8 tests)
data/                    Données brutes JSON par run (run_id = label + hash config)
journal/                 RUNS.jsonl (machine) + RUNS.md (humain)
reports/VERDICT.md       Rapport de verdict (3 branches exclusives)
```

## Démarrage

```bash
python3 tests/test_axioms.py        # conformité axiomatique
python3 scripts/run_single.py      # un run par défaut
python3 scripts/pilot.py           # campagne pilote complète
python3 scripts/campaign.py 1      # campagne complète, étage 1 (germes)
```

Aucune dépendance : Python ≥ 3.10 standard (le substrat est entier et sans PRNG ; les
instruments n'utilisent que `math` et `collections`).

## État des lieux

- Moteur, instruments, orchestration et tests : **en place** (8/8 tests axiomes).
- Campagne **complète exécutée** : 212 runs journalisés (pilote 23 + campagne 5 étages
  + confirmation longue 160 000 ticks), données brutes dans `data/`, synthèse dans
  `reports/ANALYSIS.md` (générée par `scripts/analyze.py`).
- **Verdict : NON** (`reports/VERDICT.md`). Aucun run ne coche une case du critère
  pré-enregistré. Obstruction en deux lemmes : (1) f ≤ k ⇒ vol non croissant ⇒ front O(1)
  ⇒ d ≈ 3 exige f > k (rigoureux) ; (2) f > k ⇒ effondrement « 3 couches » — reproduction
  en q·N² par tick contre une avance de front plafonnée à 1 couche/tick (A10), sans aucun
  amortissement licite (A4/A9/A12) — démontré 7/7 sur l'espace exploré. Le seul régime
  stationnaire est un **filament quasi-1D** (D_causal ≈ 1, stationnaire sur 160 000 ticks),
  sur lequel les trois contrôles négatifs sont inopérants. Frontière de validité (« à
  éprouver ») : compositions A2 à états corrélés, non explorées — voir le rapport.
