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
