# Journal de campagne — TOUS les runs (réussis, ratés, avortés)

Append-only. Une ligne par run, écrite automatiquement par
`causalnet.journal.append_runlog`. Les données brutes complètes de chaque run
sont dans `data/runs/<run_id>/`.

Légende des issues : COMPLETED (durée d'observation atteinte), EXTINCTION
(plus aucun messager), EXPLOSION (plafond de ressources machine franchi —
la dynamique n'a jamais été freinée, A9), STALLED (régime gelé : plus aucune
exécution possible).

| run_id | étiquette | paramètres | issue | ticks | événements | d_front | D_causal | d_s |
|---|---|---|---|---|---|---|---|---|
| 20260716-170235_smoke_1d8c838d | smoke | m=32 s=4 f=3 k=2 p=3 W=8 N=500 sel=0 | COMPLETED | ticks=60 | ev=1034 | d_front=nan | Dc=0.773 | ds=5.33e-05 |
| 20260716-173832_nominal_long_85810275 | nominal_long | m=32 s=4 f=3 k=2 p=3 W=8 N=600 sel=0 | STALLED | ticks=238 | ev=1435 | d_front=nan | Dc=0.816 | ds=-0 |
| 20260716-173850_M7i_compat_triviale_85810275 | M7i_compat_triviale | m=32 s=4 f=3 k=2 p=3 W=8 N=600 sel=0 | EXPLOSION | ticks=13 | ev=293100 | d_front=0.597 | Dc=1.46 | ds=0.461 |
| 20260716-174015_M7ii_sans_localite_85810275 | M7ii_sans_localite | m=32 s=4 f=3 k=2 p=3 W=8 N=600 sel=0 | STALLED | ticks=300 | ev=1483 | d_front=nan | Dc=0.818 | ds=1.51e-06 |
| 20260716-174134_M7iii_causalite_ignoree_85810275 | M7iii_causalite_ignoree | m=32 s=4 f=3 k=2 p=3 W=8 N=600 sel=0 | STALLED | ticks=238 | ev=1435 | d_front=nan | Dc=0.784 | ds=-0 |
| 20260716-174356_sweep_W=4_0e57dedf | sweep_W=4 | m=32 s=4 f=3 k=2 p=3 W=4 N=600 sel=0 | STALLED | ticks=177 | ev=753 | d_front=nan | Dc=0.755 | ds=-0 |
| 20260716-174444_sweep_W=6_e3957407 | sweep_W=6 | m=32 s=4 f=3 k=2 p=3 W=6 N=600 sel=0 | STALLED | ticks=230 | ev=980 | d_front=nan | Dc=0.771 | ds=-0 |
| 20260716-174524_nominal_v2_85810275 | nominal_v2 | m=32 s=4 f=3 k=2 p=3 W=8 N=600 sel=0 | STALLED | ticks=238 | ev=1435 | d_front=nan | Dc=0.816 | ds=-0 |
