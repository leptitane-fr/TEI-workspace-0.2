# Axiomatique fermée A1–A13

Rien à ajouter, rien à retirer. Chaque fonction du code cite l'axiome qu'elle
implémente sous la forme `[A<n>]`. Tout mécanisme sans provenance axiomatique
est une violation qui invalide le run.

## Les axiomes

- **A1 — Réseau causal.** Graphe orienté acyclique d'événements. Chaque nouvel
  événement a au moins deux causes (événements antérieurs) ; l'orientation
  passé → futur est structurelle. La dynamique ne travaille jamais sur une
  version non orientée.
- **A2 — Messagers porteurs d'état.** Chaque événement émet f ≥ 2 messagers
  (fan-out, paramètre libre), chacun porteur d'un mot de m bits (m ≥ 16).
  L'état d'un messager émis est une fonction déterministe des états des
  messagers qui ont produit l'événement.
- **A3 — Oscillation discrète.** À chaque tick, l'état de chaque messager en
  vol subit une opération déterministe inversible (rotation de bits) — période
  interne finie.
- **A4 — Exécution conditionnelle rare.** Un événement naît ssi k ≥ 2 messagers
  en vol satisfont un prédicat de compatibilité local (distance de Hamming
  ≤ s). s est libre mais jamais piloté dynamiquement.
- **A5 — Relais silencieux.** Un messager non exécuté continue : son état
  oscille, il ne stocke ni compteur de distance ni information de trajet.
- **A6 — Localité relationnelle.** Deux messagers ne sont testables que si
  leurs événements d'émission ont un ancêtre commun à profondeur ≤ p. Aucune
  coordonnée, aucun plongement, aucun mélange global.
- **A7 — Non-mémoire.** Les règles ne consultent que l'état du tick courant.
  L'historique complet n'est qu'un instrument de mesure.
- **A8 — Déterminisme intégral.** Zéro générateur pseudo-aléatoire. Toute
  diversité vient des états internes et de fonctions déterministes.
- **A9 — Flux non conservé.** Aucune conservation de masse. Interdits : gates
  thermostatiques, quotas, équilibrage naissances/morts, toute règle
  « si trop/trop peu, alors freiner/accélérer ». Explosion et extinction sont
  des résultats à documenter.
- **A10 — Tick de relais universel.** Mise à jour synchrone : un pas de relais
  par tick pour tout messager. Les périodes internes varient librement.
- **A11 — Troncature d'expérimentateur, déclarée.** Les messagers émis à
  profondeur > W derrière le front actif peuvent être retirés. W est balayé
  pour vérifier qu'aucun résultat n'en dépend.
- **A12 — Aucune finalité.** Aucune règle ne mesure ni ne corrige une grandeur
  macroscopique. Toutes les règles sont locales et myopes.
- **A13 — Dilution topologique et déphasage thermique.** La densité locale
  n'empêche aucune exécution (respect strict de A9). Lors d'une exécution,
  l'état des f messagers émis subit un déphasage algorithmique (masque XOR de
  poids contrôlé) dont la sévérité est strictement proportionnelle à la
  densité de messagers en vol dans le voisinage causal (profondeur ≤ p).
  Mécanisme purement statistique et local : dé-syntonisation naturelle en cas
  de surchauffe.

## Degrés de liberté légitimes

m, s, f, k, p, W, la transformation d'oscillation (A3), la règle de composition
des états émis (A2), la structure du prédicat de compatibilité (A4), la
fonction de déphasage proportionnelle (A13) — et la variante de germe (formule
explicite sans géométrie). **Tout autre mécanisme est interdit.**

## Interprétations opérationnelles déclarées

Ces choix d'implémentation sont déclarés ici pour l'audit ; ils n'ajoutent
aucun mécanisme hors axiomatique.

1. **Amorçage de la localité (A6) sur la soupe primordiale.** Le germe est un
   nuage de N événements *déconnectés* (aucune géométrie). Or A6 exige un
   ancêtre commun pour autoriser un test de compatibilité : un germe
   strictement déconnecté rendrait toute première exécution impossible. On
   déclare donc l'hypersurface initiale comme origine causale commune : un
   nœud formel ε (id 0, profondeur 0) est ancêtre direct de chaque événement
   du germe. ε n'émet aucun messager, ne porte aucun état et n'apparaît dans
   aucune autre règle. Dès que le front dépasse la profondeur p, ε sort de
   toutes les fenêtres de parenté : la localité relationnelle devient
   entièrement endogène. L'indépendance du régime vis-à-vis du germe
   (variantes de formule via `seed_salt`, tailles N croissantes) est testée
   en M6.
2. **Consommation des messagers exécutés (A4/A5).** Les k messagers qui
   satisfont le prédicat sont consommés par l'événement qu'ils créent ; tous
   les autres continuent (A5). Un messager participe à au plus une exécution
   par tick.
3. **Au moins deux causes (A1).** Une exécution n'est valide que si les k
   messagers proviennent d'au moins deux événements d'émission distincts ;
   sinon le groupe est ignoré (pas d'événement à cause unique).
4. **Ordre déterministe (A8).** Tout parcours (godets d'ancêtres, candidats,
   appariement glouton) suit l'ordre croissant des identifiants. Aucune
   itération sur structure non ordonnée.
5. **Densité locale (A13).** La densité vue par une exécution est le nombre de
   messagers en vol testables (au sens A6) avec le messager pivot au début du
   tick. La sévérité du déphasage est `min(m, densité × dephase_num //
   dephase_den)` bits de masque XOR — strictement proportionnelle, saturée
   uniquement par la taille physique du mot (m bits).
6. **Arrêt de ressources (instrument, pas règle).** Si la population de
   messagers dépasse un plafond de *ressources machine* (`abort_flight`,
   configuration d'expérimentateur, hors substrat), le run est **arrêté et
   journalisé comme EXPLOSION** — la dynamique n'est jamais freinée ni
   modifiée (A9). Idem pour l'extinction (plus aucun messager) : run terminé,
   résultat documenté.
7. **Profondeur (A6/A11).** La profondeur d'un événement est 1 + max des
   profondeurs de ses causes (germe : profondeur 1, sous ε à 0). Le « front
   actif » (A11) est la profondeur maximale atteinte ; la troncature retire
   les messagers dont l'événement d'émission est à plus de W couches derrière.
