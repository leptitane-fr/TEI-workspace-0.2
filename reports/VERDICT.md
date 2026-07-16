# RAPPORT DE VERDICT — dimension de croissance des réseaux causaux (A1–A12)

## Verdict : ❌ NON

**La classe de dynamiques définie par l'axiomatique A1–A12, sur l'ensemble des degrés de
liberté légitimes explorés, ne produit pas de régime spatial émergent de dimension de
croissance d ≈ 3 stable et stationnaire.** Aucun des 212 runs journalisés ne coche une seule
case du critère de succès pré-enregistré (PROTOCOL.md). Le paysage macroscopique complet se
réduit à trois sorts : **gel**, **filament quasi-1D** (seul régime stationnaire), et
**effondrement « 3 couches »**. La confrontation aux critères n'a eu lieu qu'en phase de
rapport (`scripts/analyze.py`) ; aucune valeur cible n'a jamais été présente dans le code de
génération ou de mesure (vérifié par tests d'étanchéité).

Base de preuve : `data/*.json` (212 runs bruts), `data/summary.csv`, `reports/ANALYSIS.md`,
`journal/RUNS.md` (exhaustif, aucune sélection).

---

## L'obstruction, à la manière d'un théorème

### Lemme 1 (conservation stricte — rigoureux dans l'axiomatique)

*Sous A2 (chaque événement émet exactement f messagers), A4 (chaque exécution consomme
exactement k messagers), A9 (aucune source extérieure) et A11 (la fenêtre ne fait que
retirer), le nombre de messagers en vol satisfait :*

|Vol(t)| ≤ |Vol(0)| + (f − k) · E(t),  où E(t) = nombre d'exécutions.

*Pour f ≤ k, le vol est non croissant : |Vol(t)| ≤ |Vol(0)| ≤ 8f (germe pauvre, ≤ 8
événements). Le front actif (événements d'émission des messagers en vol) est donc borné par
une constante O(1) pour tout t.*

**Conséquence :** un plateau d(r) ≈ 3 sur une décade exige N(r) ~ r³ jusqu'à r ≥ 10, donc un
front d'au moins ~10³ nœuds. Avec f ≤ k c'est impossible : **d ≈ 3 exige f > k.**

Démonstration expérimentale : 198 runs à f=k → les 46 soutenus ont tous un front ≤ 6 nœuds
et une largeur de couche ≤ 6 ; 4 runs à f<k → extinction/gel, aucun événement durable.

### Lemme 2 (étranglement de débit pour f > k — démontré expérimentalement, argument de champ moyen)

*Pour f > k : (i) A10 borne l'avance du front causal à une couche de profondeur par tick ;
(ii) les règles de composition A2 disponibles (hachage) produisent des états
approximativement uniformes, donc une probabilité de compatibilité par paire q(s, m)
constante ; (iii) au voisinage d'un germe pauvre, A6 rend tout le peuplement mutuellement
testable (ancêtres communs à profondeur ≤ p). Le taux d'exécution par tick croît donc comme
q·N², et le vol comme (f−k)·q·N² : croissance super-linéaire en tick dès que N > k/q, alors
que la hauteur croît linéairement. La largeur diverge : effondrement « 3 couches » (M4).*

*Tout mécanisme d'amortissement exigerait que q décroisse avec la densité — c'est-à-dire une
rétroaction sur une statistique de population : interdite par A4 (s fixe, jamais piloté),
A9 (pas de thermostat) et A12 (aucune mesure macroscopique dans les règles).*

Démonstration expérimentale : 9 runs à f>k — les 7 qui se sont allumés se sont tous
effondrés en ≤ 41 ticks (hauteur 12–30, largeur 778–6 474 : ratio largeur/hauteur 35–540),
sur m ∈ {32, 64}, k ∈ {2, 3}, s ∈ {12…24} ; les 2 autres n'ont jamais passé l'allumage.
**Aucun run f>k soutenu, dans aucune famille.**

### Théorème (obstruction)

*Dans la classe A1–A12 avec compositions à états quasi-uniformes : un front étendu
stationnaire exige f > k (Lemme 1) ; f > k n'admet aucun point stationnaire, faute de
mécanisme d'amortissement axiomatiquement licite (Lemme 2). Le seul régime stationnaire est
le filament conservatif f = k, de dimension causale D ≈ 1 (d ≈ 0). Donc d ≈ 3 stable et
stationnaire est impossible.*

En creux : c'est la **conjonction A9 + A12 + A4-statique** (aucune rétroaction d'aucune
sorte) avec le **plafond de débit A10** qui ferme la classe. Un espace de dimension ≥ 2
demande un front qui croît puis se stabilise ; ici tout front est soit conservé (f=k, taille
O(1)), soit multiplicatif sans frein (f>k).

### Fait annexe (rigoureux) : gel des germes déconnectés

La relation « avoir un ancêtre commun » (A6) n'est jamais créée entre composantes causales
disjointes — l'exécution qui les relierait exige déjà cet ancêtre commun. Un germe en
antichaîne pure est gelé à jamais (témoin `pilot-frozen_witness`, statut `stalled`,
0 événement dynamique). Tout germe viable contient une relation causale initiale.

---

## Le régime qui s'installe à la place : le filament

Description (46 runs soutenus, tous identiques qualitativement) : 2 à 6 messagers en vol
forment un front ponctuel qui avance d'environ 0,85 couche/tick ; le réseau causal engendré
est un fil de hauteur ≈ ticks et de largeur ≤ 6 ; **D_causal(h) = 0,99 – 1,2** (pentes
|I|(h), cohérent avec un intervalle 1D où |I| ~ h) ; pas de scaling spatial du front
(N(r) sature à r ≤ 2).

Mécanisme : à f = k = 2, chaque exécution remplace exactement la paire consommée ; seule la
portée fraîchement émise est causalement proche d'elle-même (A6), et la composition hachée
lui redonne périodiquement des paires compatibles. Le régime est un **attracteur d'une
région étendue** (robuste, M6) :

- **Germes** : les 3 germes de campagne le soutiennent (`camp-*-seed_{vee,wedge4,braid6}`).
- **s** : bande soutenue s ∈ [15 ; 24] à 20 000 ticks (m=32) ; s = 14 : durée de vie finie
  (mort à 11 021 ticks — runs `camp-filament-size-*`, journalisés) ; s ≤ 13 : extinction.
- **W ∈ {4…128}** : sorts et mesures inchangés (indépendance à la troncature A11 vérifiée).
- **p ∈ {1…5}**, **m ∈ {16, 24, 32}** (m ≥ 48 : gel à s fixé — l'allumage exige s ~ m/2 − c),
  **2 oscillations, 2 compositions, 2 prédicats** : filament partout où ça s'allume.
- Stationnarité longue : run de confirmation `camp-filament-long_s16` (160 000 ticks visés).

**Contrôles négatifs (M7) — constat obligatoire :** les trois contrôles (prédicat trivial,
p = ∞, causalité ignorée) **ne cassent pas le filament** (`camp-*-ctrl_*`). Avec ≤ 6
messagers en vol, la rareté (A4) et la localité (A6) ne contraignent plus rien : dans le
seul régime stationnaire de la classe, les ingrédients constitutifs de l'axiomatique **ne
font rien**. C'est la signature qu'aucun espace n'y est construit — et, par le critère 6
pré-enregistré, ce régime serait disqualifié même à bonne dimension.

---

## Expériences clés (identifiants de runs)

| Fait | Runs |
|---|---|
| Lemme 1 (f=k ⇒ front O(1)) | les 46 soutenus de `data/summary.csv` (largeur ≤ 6) |
| Lemme 2 (f>k ⇒ effondrement) | `camp-filament-f_3`, `camp-filament-f_4`, `camp-triadic-k_2`, `camp-triadic-f_4`, `camp-wide_state-f_3`, `camp-wide_state-f_4`, `pilot-f_3` |
| f<k ⇒ extinction | `camp-triadic-f_2`, `camp-filament-k_3` |
| Gel des germes déconnectés (A6) | `pilot-frozen_witness` |
| Indépendance à W | `camp-{filament,wide_state,blocks,triadic}-W_{4..128}` |
| Bande s du filament / durée de vie finie s=14 | `camp-filament-s_{8..24}`, `camp-filament-size-*` |
| Contrôles ne cassant pas le filament | `camp-*-ctrl_{trivial,p_inf,no_causality}` |

Répartition globale des sorts (212 runs) : gel 152 · soutenu (filament) 46 · explosion 7 ·
moribond 6. Candidats satisfaisant c1–c4 : **aucun** (`reports/ANALYSIS.md`).

---

## Frontière de validité du verdict (« à éprouver »)

Le Lemme 1 est rigoureux dans l'axiomatique. Le Lemme 2 est démontré sur l'espace exploré
(2 familles de composition, 2 prédicats, 2 oscillations, m ≤ 64, k ≤ 3, 212 runs) et étayé
par l'argument de champ moyen ; il n'est **pas** un théorème pour toute règle de composition
concevable. La seule échappatoire logique identifiée serait une composition A2 qui corrèle
délibérément les états émis pour que la probabilité de compatibilité effective décroisse
avec la densité locale **par pure statistique d'états** (sans mesure de population, donc
licite). Aucune des compositions testées (toutes hachantes, donc uniformisantes) n'a ce
caractère ; construire une telle composition — et vérifier qu'elle ne gèle pas l'allumage,
qui exige au contraire une compatibilité accessible à ~10 messagers — est la première cible
d'une campagne future. Le critère pré-enregistré (« toutes les cases, sinon NON ») rend le
présent verdict NON indépendamment de cette frontière, qui borne le domaine *démontré* de
l'obstruction, pas le verdict.

## Conformité au protocole

- 3 germes ✓ · balayage complet de chaque paramètre libre ✓ · W ✓ · tailles croissantes ✓
  (jusqu'à 320 000 ticks demandés ; les runs meurent ou tiennent bien avant les caps) ·
  contrôles négatifs ✓ (résultat : inopérants sur le filament — dit ci-dessus).
- RÈGLE D'OR : étanchéité génération/mesure vérifiée par test ; détection de plateau
  agnostique ; critères confrontés uniquement ici et dans `scripts/analyze.py`.
- Journal exhaustif : 212 entrées, y compris gels, explosions et abandons de ressources.
- Aucun exposant « séduisant » à signaler : aucun plateau spatial n'existe, en aucune
  configuration.
