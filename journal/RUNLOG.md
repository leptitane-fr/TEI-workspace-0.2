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
| 20260716-174555_sweep_W=8_85810275 | sweep_W=8 | m=32 s=4 f=3 k=2 p=3 W=8 N=600 sel=0 | STALLED | ticks=238 | ev=1435 | d_front=nan | Dc=0.816 | ds=-0 |
| 20260716-174856_sweep_W=12_7eb2fec8 | sweep_W=12 | m=32 s=4 f=3 k=2 p=3 W=12 N=600 sel=0 | STALLED | ticks=301 | ev=1845 | d_front=nan | Dc=0.821 | ds=3.07e-12 |
| 20260716-175305_sweep_W=16_993c944f | sweep_W=16 | m=32 s=4 f=3 k=2 p=3 W=16 N=600 sel=0 | STALLED | ticks=355 | ev=2272 | d_front=nan | Dc=0.853 | ds=-0 |
| 20260716-175420_sweep_s=1_6586b68d | sweep_s=1 | m=32 s=1 f=3 k=2 p=3 W=8 N=600 sel=0 | STALLED | ticks=160 | ev=630 | d_front=nan | Dc=nan | ds=-0 |
| 20260716-180142_sweep_W=24_aa79817d | sweep_W=24 | m=32 s=4 f=3 k=2 p=3 W=24 N=600 sel=0 | COMPLETED | ticks=400 | ev=3104 | d_front=nan | Dc=0.897 | ds=8.53e-07 |
| 20260716-180251_sweep_seed_N=500_1d8c838d | sweep_seed_N=500 | m=32 s=4 f=3 k=2 p=3 W=8 N=500 sel=0 | STALLED | ticks=256 | ev=1142 | d_front=nan | Dc=0.825 | ds=1.37e-09 |
| 20260716-180401_sweep_seed_N=600_85810275 | sweep_seed_N=600 | m=32 s=4 f=3 k=2 p=3 W=8 N=600 sel=0 | STALLED | ticks=238 | ev=1435 | d_front=nan | Dc=0.816 | ds=-0 |
| 20260716-180517_sweep_s=2_215dfe79 | sweep_s=2 | m=32 s=2 f=3 k=2 p=3 W=8 N=600 sel=0 | STALLED | ticks=160 | ev=635 | d_front=nan | Dc=nan | ds=-0 |
| 20260716-180546_sweep_seed_N=800_4ff057e2 | sweep_seed_N=800 | m=32 s=4 f=3 k=2 p=3 W=8 N=800 sel=0 | STALLED | ticks=227 | ev=2308 | d_front=0.0496 | Dc=0.822 | ds=2.05e-06 |
| 20260716-180811_sweep_seed_N=1000_c551f9a6 | sweep_seed_N=1000 | m=32 s=4 f=3 k=2 p=3 W=8 N=1000 sel=0 | STALLED | ticks=237 | ev=3050 | d_front=0.335 | Dc=0.813 | ds=0.00225 |
| 20260716-180917_sweep_seed_salt=0_85810275 | sweep_seed_salt=0 | m=32 s=4 f=3 k=2 p=3 W=8 N=600 sel=0 | STALLED | ticks=238 | ev=1435 | d_front=nan | Dc=0.816 | ds=-0 |
| 20260716-181105_sweep_seed_salt=1_8a0f5166 | sweep_seed_salt=1 | m=32 s=4 f=3 k=2 p=3 W=8 N=600 sel=1 | STALLED | ticks=279 | ev=1619 | d_front=nan | Dc=0.823 | ds=6.38e-09 |
| 20260716-181302_sweep_seed_salt=2_465e42ba | sweep_seed_salt=2 | m=32 s=4 f=3 k=2 p=3 W=8 N=600 sel=2 | STALLED | ticks=272 | ev=1678 | d_front=nan | Dc=0.82 | ds=3.56e-08 |
| 20260716-181407_sweep_seed_salt=3_aa3b3ada | sweep_seed_salt=3 | m=32 s=4 f=3 k=2 p=3 W=8 N=600 sel=3 | STALLED | ticks=256 | ev=1494 | d_front=nan | Dc=0.834 | ds=2.86e-13 |
| 20260716-181515_sweep_rot_rule=rotl_step_85810275 | sweep_rot_rule=rotl_step | m=32 s=4 f=3 k=2 p=3 W=8 N=600 sel=0 | STALLED | ticks=238 | ev=1435 | d_front=nan | Dc=0.816 | ds=-0 |
| 20260716-181713_sweep_s=3_1d6355d4 | sweep_s=3 | m=32 s=3 f=3 k=2 p=3 W=8 N=600 sel=0 | STALLED | ticks=197 | ev=670 | d_front=nan | Dc=nan | ds=-0 |
| 20260716-181819_sweep_s=4_85810275 | sweep_s=4 | m=32 s=4 f=3 k=2 p=3 W=8 N=600 sel=0 | STALLED | ticks=238 | ev=1435 | d_front=nan | Dc=0.816 | ds=-0 |
| 20260716-181859_sweep_s=6_eee38109 | sweep_s=6 | m=32 s=6 f=3 k=2 p=3 W=8 N=600 sel=0 | STALLED | ticks=394 | ev=15652 | d_front=nan | Dc=1.08 | ds=-0 |
| 20260716-182251_sweep_rot_rule=rotl_1_471f1ab0 | sweep_rot_rule=rotl_1 | m=32 s=4 f=3 k=2 p=3 W=8 N=600 sel=0 | STALLED | ticks=130 | ev=616 | d_front=nan | Dc=nan | ds=-0 |
| 20260716-182400_sweep_compose_rule=fold_xor_rot_85810275 | sweep_compose_rule=fold_xor_rot | m=32 s=4 f=3 k=2 p=3 W=8 N=600 sel=0 | STALLED | ticks=238 | ev=1435 | d_front=nan | Dc=0.816 | ds=-0 |
| 20260716-182502_sweep_compose_rule=fold_add_rot_633c7693 | sweep_compose_rule=fold_add_rot | m=32 s=4 f=3 k=2 p=3 W=8 N=600 sel=0 | STALLED | ticks=241 | ev=1445 | d_front=nan | Dc=0.827 | ds=9.09e-13 |
