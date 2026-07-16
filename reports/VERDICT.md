# RAPPORT DE VERDICT — dimension de croissance des réseaux causaux (A1–A12)

## Verdict : ⬜ NON PRONONCÉ (campagne complète non exécutée)

Ce rapport sera rempli exclusivement à partir des données brutes de `data/` et du journal
exhaustif `journal/RUNS.md`, confrontées aux critères pré-enregistrés de `PROTOCOL.md`.
Les trois branches possibles sont exclusives :

- **OUI** — d de croissance du front ∈ [2,7 ; 3,3] en plateau (< 10 %) sur ≥ 1 décade,
  stationnaire (M5), d_s concordante (< 15 %), D_causal ≈ d + 1 (< 15 %), robuste
  (≥ 3 germes, région étendue, indépendance à W), les trois contrôles négatifs cassent.
  → livrer : règle exacte, provenance axiomatique, analyse du POURQUOI, sensibilité.
- **NON** — obstruction énoncée à la manière d'un théorème + expériences qui la
  démontrent + régime qui s'installe à la place.
- **INDÉTERMINÉ** — uniquement par manque de ressources ; dire exactement ce qui manque.

---

## Faits établis à ce stade (pilote de validation — pas de verdict)

Toutes les affirmations ci-dessous renvoient à des runs journalisés (aucune sélection).

### F1 — Gel des germes causalement déconnectés (conséquence structurelle de A6)

Énoncé (démontrable depuis l'axiomatique) : *si deux événements n'ont aucun ancêtre commun,
aucune règle ne peut jamais tester leurs messagers en compatibilité (A6) ; la relation
« avoir un ancêtre commun » n'est créée que par exécution, qui exige ce même ancêtre
commun. Donc les composantes causalement disjointes du germe n'interagissent jamais.*
Corollaire : un germe en antichaîne pure est gelé à jamais. Vérifié par le témoin
`antichain2` (statut `stalled`, 0 événement dynamique). Conséquence de conception : tout
germe de campagne contient au moins une relation causale initiale.

### F2 — Paysage à trois sorts de la famille Hamming (m=32, k=2, germe vee)

Sondage initial (runs `pilot-*`, voir journal) :

| Région | Sort | Description |
|---|---|---|
| f=3, s ≥ 8 | **explosion** | croissance nette +1 messager/exécution ; paires candidates en O(n²) ; abandon de ressources en ~10² ticks |
| f=3, s ≤ 7 | **gel** | jamais d'allumage (périodes jointes épuisées sans compatibilité) |
| f=2, s ≈ 13–16 | **filament soutenu** | ~4-6 messagers en vol, profondeur linéaire en tick, D_causal(h) ≈ 1,0 : régime quasi-1D stationnaire |
| f=2, s ≤ 12 | **extinction/gel** | allumage puis mort, ou pas d'allumage |

Le seul régime stationnaire identifié à ce stade est **unidimensionnel** (filament).
Ce n'est PAS un verdict : l'espace (m, prédicats par blocs, k=3, compositions alternatives,
germes, tailles) n'a été que très partiellement sondé, aux tailles pilotes uniquement.

### F3 — Robustesse et contrôles du régime filament (pilote, 23 runs journalisés)

- **Indépendance au germe** : les trois germes de campagne (`vee`, `wedge4`, `braid6`)
  soutiennent le filament (5 300 / 6 146 / 14 325 événements en 3 000 ticks).
- **Région, pas point réglé** : bande soutenue s ∈ [12 ; 18] à f=2 (extinction à s ≤ 10) ;
  insensible à W ∈ {8, 16, 32, 64} et à p ∈ {3, 4} (p=2 : filament plus maigre, soutenu).
- **MAIS les trois contrôles négatifs NE CASSENT PAS le régime filament** : prédicat
  trivial, p = ∞ et causalité ignorée produisent tous un filament comparable. Lecture
  honnête : avec ~4-6 messagers en vol, la rareté (A4) et la localité (A6) ne contraignent
  plus rien — le filament est un régime où ces ingrédients « ne font rien ». Conséquence
  pré-enregistrée : même si sa dimension avait été dans la cible, ce régime échouerait au
  critère 6. Tout régime candidat devra maintenir un front étendu où ces ingrédients
  travaillent réellement.

### Points de vigilance déjà identifiés pour la campagne

1. **Tension A9 vs stationnarité étendue** : sans conservation ni thermostat, un régime
   stationnaire à front étendu exige un équilibre auto-organisé entre reproduction
   (exécutions, +f−k) et pertes (fenêtre A11 / dilution). Le pilote n'a observé cet
   équilibre que dans le régime filament (front minimal). À éprouver : existe-t-il une
   région de paramètres où l'équilibre se fait à front LARGE ? Si la réponse est non et
   démontrable, c'est le cœur d'un verdict NON.
2. **Dépendance à W interdite** : si un régime ne tient que pour une fenêtre W précise,
   il dépend de la troncature d'expérimentateur (A11) — disqualifiant, à documenter.
3. **Criticité réglée vs attracteur** : la frontière gel/explosion est abrupte ; un régime
   qui n'existe que sur la frontière est un « point réglé » (curseur), pas un attracteur —
   le balayage M6 tranchera plateau vs curseur.

## Ce qui manque pour prononcer le verdict

- Exécution des étages 1–5 de `scripts/campaign.py` (balayages complets m, s, f, k, p,
  osc, composition, prédicat ; W ; tailles croissantes ; ≥ 3 germes ; contrôles négatifs
  sur chaque régime candidat).
- Analyse de stationnarité M5 (transitoire identifié, tenue ≥ 10 × transitoire) sur tout
  régime soutenu trouvé.
- Confrontation aux critères pré-enregistrés, uniquement en phase de rapport.
