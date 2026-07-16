# PROTOCOLE PRÉ-ENREGISTRÉ — Campagne « dimension de croissance des réseaux causaux »

**Statut : figé avant campagne.** Toute modification ultérieure de ce document doit être
tracée par commit et justifiée par la conformité axiomatique, jamais par un résultat de mesure.

## Mission

Déterminer si la classe de dynamiques définie par l'axiomatique A1–A12 peut produire un
régime spatial émergent de dimension de croissance **d ≈ 3, stable et stationnaire**, et livrer
un verdict tranché : **OUI** (mécanisme), **NON** (obstruction), ou **INDÉTERMINÉ** (manque exact).

## RÈGLE D'OR (anti-ajustement, non négociable)

La cible d ≈ 3 est connue de l'expérimentateur mais **n'entre jamais dans le système** :
aucune règle, aucun paramètre, aucun seuil n'encode un exposant visé, une dimension, un
diamètre cible ou une correction dépendant d'une mesure macroscopique.

- L'itération sur les règles est permise ; son **critère est la conformité axiomatique et la
  stabilité** (existence d'un plateau stationnaire, quelle qu'en soit la valeur) — jamais la
  valeur de l'exposant.
- Génération et mesure sont **étanches** : `engine.py`/`seeds.py`/`params.py` (substrat)
  n'importent jamais `measures.py`/`runner.py`/`journal.py`/`sweep.py` (expérimentateur).
  Vérifié mécaniquement par `tests/test_axioms.py::test_etancheite_generation_mesure`.
- Chaque fonction du code est annotée de l'axiome qu'elle implémente (A1–A12) ; tout
  mécanisme sans provenance axiomatique = violation = run invalide. Voir `AUDIT.md`.

## L'AXIOMATIQUE (fermée — rien à ajouter, rien à retirer)

- **A1 — Réseau causal.** Graphe orienté acyclique d'événements. Chaque nouvel événement a
  au moins deux causes (événements antérieurs) ; orientation passé→futur structurelle. La
  dynamique ne travaille jamais sur une version non orientée (les projections non orientées
  ne servent qu'aux mesures de l'expérimentateur).
- **A2 — Messagers porteurs d'état.** Chaque événement émet f ≥ 2 messagers (fan-out,
  paramètre libre), chacun porteur d'un mot de m bits (m ≥ 16). L'état émis est une fonction
  déterministe des états des messagers qui ont produit l'événement (règle de composition :
  degré de liberté).
- **A3 — Oscillation discrète.** À chaque tick, l'état de chaque messager en vol subit une
  opération déterministe inversible (rotation, permutation) — période interne finie.
- **A4 — Exécution conditionnelle rare.** Un événement naît ssi k ≥ 2 messagers en vol
  satisfont un prédicat de compatibilité local sur leurs états (ex. Hamming ≤ s). La
  compatibilité doit être rare ; s est libre mais il est interdit de le piloter dynamiquement.
- **A5 — Relais silencieux.** Un messager non exécuté continue : son état oscille, il ne
  stocke ni compteur de distance ni information de trajet.
- **A6 — Localité relationnelle.** Deux messagers ne sont testés que si leurs événements
  d'émission ont un ancêtre commun à profondeur ≤ p (p petit, fixe, libre). Aucune
  coordonnée, aucun plongement, aucun mélange global, aucune statistique globale.
- **A7 — Non-mémoire.** Les règles ne consultent que le tick courant (front actif +
  messagers en vol). L'historique complet est un instrument de mesure, jamais une entrée
  des règles.
- **A8 — Déterminisme intégral.** Zéro PRNG, partout, y compris à l'initialisation. Toute
  diversité vient des états internes et de fonctions déterministes (hachage).
- **A9 — Flux non conservé.** Aucune conservation de masse. Interdits : gates
  thermostatiques, quotas, équilibrage naissances/morts, toute règle « si trop/trop peu,
  freiner/accélérer ». Explosion et extinction sont des résultats à documenter.
- **A10 — Tick de relais universel.** Mise à jour des vols synchrone : un pas de relais par
  tick pour tout messager. Les périodes internes (A3) varient librement par messager.
- **A11 — Troncature d'expérimentateur, déclarée.** Les messagers émis à profondeur > W
  derrière le front actif peuvent sortir du domaine simulé. W est une commodité
  d'implémentation, pas une règle : balayé pour vérifier qu'aucun résultat n'en dépend.
- **A12 — Aucune finalité.** Aucune règle ne mesure ni ne corrige une grandeur
  macroscopique. Toutes les règles sont locales et myopes.

## Degrés de liberté légitimes (seul espace de créativité)

m, s, f, k, p, W, transformation d'oscillation (A3), règle de composition (A2), structure du
prédicat (A4). Tout autre mécanisme est interdit.

## Germes (obligatoirement pauvres)

≥ 3 germes structurellement différents, 2 à 8 événements, états par formule explicite,
**aucune géométrie encodée**. Germes de campagne : `vee` (3 év.), `wedge4` (4 év.),
`braid6` (6 év.) ; témoin structurel : `antichain2` (gelé par A6, démonstration).

## Mesures obligatoires

- **M1 — Dimension causale.** |I(p,q)| ~ h^D + estimateur de Myrheim-Meyer. Attendu si un
  espace-temps émerge : D_causal ≈ d + 1.
- **M2 — Espace du front.** Graphe de proximité (MRCA ≤ p), BFS ≥ 10 sources
  déterministes, publication de N(r) et de la série complète d(r).
- **M3 — Dimension spectrale.** P(t) ~ t^(−d_s/2), itération déterministe de la matrice de
  transition (marche paresseuse).
- **M4 — Hauteur vs largeur** (détection d'effondrement type « 3 couches »).
- **M5 — Stationnarité.** Toutes mesures en fonction du tick ; transitoire identifié,
  rapporté, exclu ; tenue sans dérive sur ≥ 10 × le transitoire.
- **M6 — Robustesse.** Balayage complet de chaque paramètre libre (plateau vs curseur),
  ≥ 3 germes, tailles croissantes, balayage de W.
- **M7 — Contrôles négatifs** (chacun doit dégrader ou casser le régime, sinon le dire) :
  (i) compatibilité triviale ; (ii) p = ∞ ; (iii) causalité ignorée.

## Critère de succès (pré-enregistré — toutes les cases, sinon verdict NON)

1. d de croissance du front ∈ **[2,7 ; 3,3]**, en plateau (variation < 10 %) sur ≥ 1 décade
   de r avant effets de bord ;
2. stationnaire (M5) ;
3. dimension spectrale concordante (écart < 15 %) ;
4. D_causal ≈ d + 1 (écart < 15 %) ;
5. robuste : ≥ 3 germes, région étendue de l'espace des paramètres, indépendance à W ;
6. les trois contrôles négatifs cassent ou dégradent le régime.

Un « presque » (plateau stable à 2,4 ou 3,8) est un verdict **NON pour la cible**, à
rapporter tel quel avec le mécanisme du régime réellement obtenu.

**Note d'étanchéité :** les bornes ci-dessus ne sont utilisées QUE dans la phase de rapport
(comparaison des mesures publiées aux critères). Aucun code de génération, de mesure ou
d'orchestration ne les contient — la détection de plateau (`measures.plateau`) est
agnostique de toute valeur.

## Verdict exigé — trois branches exclusives

- **OUI** : règle exacte, provenance axiomatique de chaque mécanisme, analyse du POURQUOI,
  sensibilité complète, les trois contrôles négatifs qui cassent.
- **NON** : obstruction énoncée à la manière d'un théorème, expériences qui la démontrent,
  régime qui s'installe à la place.
- **INDÉTERMINÉ** : uniquement si les ressources n'ont pas permis de trancher — dire
  exactement ce qui manque.

## Livraison

Code complet commenté (fonction → axiome), données brutes (`data/*.json` : N(r), d(r),
P(t), |I|(h), tables de balayage, tout en fonction du tick), journal exhaustif de TOUS les
runs y compris ratés (`journal/`), rapport de verdict (`reports/VERDICT.md`). Tout exposant
qui « tombe juste » est signalé « à éprouver » et soumis à sensibilité avant d'être rapporté.
