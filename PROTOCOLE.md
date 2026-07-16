# Protocole de mesure et critère de succès pré-enregistré

Ce document est figé AVANT la campagne. La cible d ≈ 3 n'apparaît qu'ici et
dans le rapport — jamais dans le substrat (règle d'or, cf. `README.md`).

## Mesures obligatoires

- **M1 — Dimension causale.** Scaling du volume des intervalles causaux
  |I(p,q)| ~ h^D sur le DAG (h = longueur de la plus longue chaîne p→q).
  Rapporter D_causal (ajustement log-log + exposants locaux).
  Instrument : `measure.m1_causal_intervals`.
- **M2 — Espace du front.** Graphe de proximité du front (événements des
  dernières couches, adjacence = ancêtre commun à profondeur ≤ p, même
  relation que A6 mais utilisée en lecture seule). BFS multi-sources :
  publier N(r) et la série complète des exposants locaux d(r).
  Instrument : `measure.m2_front_growth`.
- **M3 — Dimension spectrale du front.** Marche paresseuse déterministe
  (itération exacte du vecteur de probabilité) : P(t) ~ t^(−d_s/2), série
  d_s(t). Instrument : `measure.m3_spectral`.
- **M4 — Hauteur vs largeur** du réseau causal (profil des couches).
  Instrument : `measure.m4_height_width`.
- **M5 — Stationnarité.** Toutes les mesures en fonction du tick
  (checkpoints) ; transitoire identifié et exclu avant tout ajustement.
- **M6 — Robustesse.** Balayage complet de chaque paramètre libre (m, s, f,
  k, p, W, variantes A3/A2/A13, germe : N et sel) ; tailles croissantes.
  Script : `scripts/run_sweep.py`.
- **M7 — Contrôles négatifs** (chacun doit dégrader ou casser le régime) :
  (i) compatibilité triviale (s = m) ; (ii) localité retirée (p = ∞) ;
  (iii) causalité ignorée (parenté des nouveaux événements décorrélée des
  messagers exécutés). Script : `scripts/run_controls.py`.

## Critère de succès (toutes les cases, sinon verdict NON)

1. d de croissance du front dans **[2,7 ; 3,3]** ;
2. en **plateau** (variation < 10 %) sur au moins **une décade de r** avant
   effets de bord ;
3. **stationnaire** (M5 : plateau maintenu hors transitoire) ;
4. dimension spectrale **concordante** (écart < 15 % avec d) ;
5. **D_causal ≈ d + 1** ;
6. **robuste** (M6 : le régime survit aux balayages, aucun résultat ne dépend
   de W) ;
7. les trois **contrôles négatifs échouent** (le régime se dégrade ou casse).

Un « presque » est un verdict **NON**, à rapporter tel quel avec son mécanisme.

## Règles de campagne

- Chaque run (réussi, raté, avorté) est journalisé dans `journal/RUNLOG.md`
  et ses données brutes archivées dans `data/runs/<run_id>/`.
- `scripts/audit_etancheite.py` doit passer avant toute campagne ; le rapport
  final est audité ligne à ligne contre l'axiomatique.
- L'itération sur les règles n'est permise que pour (a) la conformité
  axiomatique, (b) l'obtention d'un régime physique stationnaire. Jamais pour
  rapprocher un exposant de la cible.
- Explosion et extinction ne sont pas des échecs d'implémentation : ce sont
  des résultats (A9), documentés avec leurs paramètres.
