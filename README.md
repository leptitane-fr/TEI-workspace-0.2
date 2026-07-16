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

## État des lieux (mis à jour à chaque étape)

- Moteur, instruments, orchestration et tests : **en place** (8/8 tests axiomes).
- Campagne **pilote** exécutée (23 runs journalisés, données dans `data/`) :
  - un germe sans relation causale est **gelé à jamais** (conséquence prouvable de A6) ;
  - la dynamique de référence (m=32, Hamming) présente un paysage à trois sorts :
    gel, **filament quasi-1D soutenu** (f=2, s ∈ [12;18], indépendant du germe et de W),
    explosion (f=3, s≥8) ;
  - constat M7 : les contrôles négatifs ne cassent PAS le régime filament (rareté et
    localité n'y travaillent plus) — détail dans `reports/VERDICT.md`.
- Verdict : **non prononcé** — campagne complète à exécuter (`scripts/campaign.py`).
