# AUDIT — provenance axiomatique de chaque mécanisme

Table de correspondance fonction → axiome(s). Tout mécanisme sans ligne ici est une
violation (run invalide). Les annotations `[A#]` figurent aussi dans les docstrings.

## Substrat (la dynamique — entier, déterministe, myope)

| Fonction | Fichier | Axiome(s) | Rôle |
|---|---|---|---|
| `mix64` | engine.py | A8 | Hachage entier déterministe — unique source de diversité |
| `rotl` | engine.py | A3 | Rotation de bits, inversible, période finie |
| `EventRecord` | engine.py | A1 | Événement du DAG causal (≥ 2 causes si non racine) |
| `Messenger` | engine.py | A2, A5, A6 | État m bits + ancêtres ≤ p ; ni compteur ni trajet |
| `_osc_rot_birth` | engine.py | A3, A10 | Oscillation : rotation de pas propre (périodes libres) |
| `_osc_rot1_xor` | engine.py | A3 | Oscillation : affine inversible sur F2^m |
| `_pred_hamming` | engine.py | A4 | Prédicat local : Hamming ≤ s |
| `_pred_block_zero` | engine.py | A4 | Prédicat local : ≥ s blocs de 8 bits nuls dans le XOR |
| `_compose_fold_rot_xor` | engine.py | A2 | Composition déterministe des états exécutés |
| `_compose_fold_mul_add` | engine.py | A2 | Composition alternative (famille distincte) |
| `child_state` | engine.py | A2 | État émis = fonction déterministe (graine, branche) |
| `birth_rot` | engine.py | A3, A8 | Pas de rotation propre dérivé de l'état de naissance |
| `Engine.__init__` | engine.py | A1–A12 | Assemblage ; aucun PRNG, aucune statistique globale |
| `Engine.add_seed_event` | engine.py | A8, A1 | Données initiales par formule ; ≥ 2 causes si non racine |
| `Engine.step` | engine.py | A10, A3, A4 | Tick synchrone : oscillation puis exécution rare |
| `Engine.apply_window` | engine.py | A11 | Troncature d'expérimentateur déclarée (W balayé) |
| `Engine._candidate_compatible_pairs` | engine.py | A6, A4, A8 | Seaux par ancêtre ≤ p ; ordre canonique ; contrôles M7 |
| `Engine._greedy_match` | engine.py | A4, A8, A1 | Appariement k-groupe glouton déterministe, ≥ 2 causes |
| `Engine._child_anc_levels` | engine.py | A6, A7 | Ancêtres ≤ p transportés localement (jamais l'historique) |
| `Engine._execute` | engine.py | A1, A2, A9 | Création d'événement, émission f messagers, zéro conservation |
| `Params` | params.py | — | Degrés de liberté déclarés + caps de ressources (pas des règles) |
| `_formula_state` | seeds.py | A8 | États de germe par formule explicite |
| `seed_vee`, `seed_wedge4`, `seed_braid6` | seeds.py | A8, A1 | Germes pauvres sans géométrie |
| `seed_antichain2` | seeds.py | A8 | Témoin gelé (démonstration structurelle A6) |
| `build_engine` | seeds.py | A8 | Initialisation intégralement déterministe |

## Points d'audit sensibles (justifications)

- **Caps `max_*` (params.py)** : limites de RESSOURCES d'expérimentateur. Ils *arrêtent
  l'observation* (statut `explosion_*`/`candidate_explosion` journalisé), ils ne modifient
  jamais une probabilité d'exécution ni un flux (conformité A9/A12). Aucun cap n'est
  déclenché par une grandeur macroscopique mesurée — uniquement par le coût de calcul.
- **`stall_ticks`** : détection d'arrêt d'observation quand plus rien ne peut se produire
  (états périodiques, A3) — n'influence pas la dynamique.
- **`Engine.max_depth`** : compteur utilisé UNIQUEMENT par `apply_window` (A11, troncature
  déclarée) — jamais par une règle de naissance/mort ou de compatibilité.
- **`Messenger.roots`** : consommé uniquement par le contrôle négatif M7-ii (p = ∞) ;
  la dynamique nominale ne le lit pas.
- **Ordre canonique des appariements** : tri par identifiants (ordre de création) — requis
  par A8 (déterminisme intégral), n'encode aucune préférence macroscopique.

## Expérimentateur (instruments — jamais importés par le substrat)

| Fonction | Fichier | Mesure | Rôle |
|---|---|---|---|
| `even_sources` | measures.py | M2, M3 | Sources BFS déterministes |
| `front_proximity_graph` | measures.py | M2 | Graphe du front (MRCA ≤ p), recalculé de l'historique |
| `bfs_growth` | measures.py | M2 | N(r) et série complète d(r) |
| `spectral_return` | measures.py | M3 | P(t), d_s(t) par itération déterministe |
| `causal_intervals`, `_interval`, `_ordering_fraction` | measures.py | M1 | |I|(h), D(h), fraction d'ordre |
| `mm_ordering_fraction`, `mm_dimension` | measures.py | M1 | Estimateur de Myrheim-Meyer |
| `height_width` | measures.py | M4 | Profil hauteur/largeur |
| `plateau` | measures.py | M5, M6 | Détection de plateau agnostique de toute cible (RÈGLE D'OR) |
| `children_map` | measures.py | M1 | Carte enfants (instrument) |
| `runner.run` | runner.py | M5 | Boucle d'observation, séries par tick, checkpoints |
| `runner._checkpoint_measures` | runner.py | M2–M4 | Mesures périodiques (garde-fous de ressources déclarés) |
| `journal.append` | journal.py | — | Journal exhaustif append-only (tous les runs) |
| `sweep.run_seed_battery` | sweep.py | M6 | ≥ 3 germes |
| `sweep.run_param_sweep` | sweep.py | M6 | Plateau vs curseur, y compris W (A11) |
| `sweep.run_negative_controls` | sweep.py | M7 | Les trois contrôles pré-enregistrés |

## Vérifications mécaniques (tests/test_axioms.py)

- A8 : déterminisme intégral (double run identique) ; zéro import de PRNG.
- A3 : oscillations inversibles à période finie (cycle sans pré-période).
- A1 : ≥ 2 causes distinctes, orientation passé→futur (profondeur strictement croissante).
- A5 : slots du messager audités (aucun champ de trajet/distance).
- A12 : `engine.py` sans aucune constante flottante (substrat entier).
- RÈGLE D'OR : étanchéité substrat/instruments vérifiée sur les imports.
