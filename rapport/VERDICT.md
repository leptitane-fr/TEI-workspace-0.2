# RAPPORT DE VERDICT

**Question pré-enregistrée.** La classe de dynamiques définie par
l'axiomatique fermée A1–A13 (`AXIOMES.md`) peut-elle produire un régime
spatial émergent de dimension de croissance d ≈ 3, stable et stationnaire,
au sens du critère de succès pré-enregistré (`PROTOCOLE.md`) ?

**Statut : INDÉTERMINÉ — campagne non encore exécutée.**

Le présent dépôt est en phase d'infrastructure : substrat, instruments,
contrôles, audit et journal sont en place et validés (audit d'étanchéité,
tests de conformité, smoke test de bout en bout). Aucun run de campagne
(M5 longue durée, balayages M6, contrôles M7 aux tailles nominales) n'a
encore été exécuté ni analysé : aucune des trois branches ne peut être
honnêtement cochée.

Ce qui manque exactement pour trancher :

1. runs nominaux longs (M5) avec transitoire identifié et exclu ;
2. table M6 complète (chaque axe de `scripts/run_sweep.py`, tailles
   croissantes, indépendance en W démontrée) ;
3. table M7 (les trois contrôles négatifs doivent chacun dégrader ou casser
   le régime) ;
4. confrontation des séries d(r), d_s(t), D_causal(h) au critère
   pré-enregistré, cases cochées une à une.

---

## Verdict (trois branches exclusives — une seule sera retenue)

### ☐ OUI
- Règle exacte (paramètres et variantes A2/A3/A4/A13) : _à remplir_
- Provenance axiomatique de chaque mécanisme : _à remplir_
- Analyse du POURQUOI (mécanisme de l'émergence) : _à remplir_
- Contrôles négatifs qui cassent (M7 i/ii/iii) : _à remplir_

### ☐ NON
- Obstruction la plus précise possible (théorème ou argument) : _à remplir_
- Expériences à l'appui (run_ids) : _à remplir_
- Régime qui s'installe à la place : _à remplir_

### ☒ INDÉTERMINÉ (état actuel)
- Ce qui manque : les points 1–4 ci-dessus (campagne complète non exécutée).

---

## Grille du critère pré-enregistré (à cocher avec preuves)

| # | Critère | Statut | Preuve (run_id / fichier) |
|---|---|---|---|
| 1 | d_front ∈ [2,7 ; 3,3] | ☐ | |
| 2 | plateau (< 10 %) sur ≥ 1 décade de r | ☐ | |
| 3 | stationnaire (M5, transitoire exclu) | ☐ | |
| 4 | d_s concordante (écart < 15 %) | ☐ | |
| 5 | D_causal ≈ d + 1 | ☐ | |
| 6 | robustesse M6 (dont indépendance en W) | ☐ | |
| 7 | M7 : les trois contrôles cassent | ☐ | |

Rappel : un « presque » est un verdict **NON**, à rapporter tel quel avec son
mécanisme propre.
