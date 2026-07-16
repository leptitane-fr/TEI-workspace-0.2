"""causalnet — campagne « dimension de croissance émergente » (axiomes A1–A13).

Modules :
- params    : degrés de liberté légitimes + config d'expérimentateur ;
- substrate : la dynamique, étanche et annotée axiome par axiome ;
- seeds     : soupe primordiale par formule explicite (zéro géométrie) ;
- controls  : contrôles négatifs M7 (substrats volontairement cassés) ;
- measure   : instruments M1–M5 (lecture seule) ;
- runner    : orchestration des runs instrumentés ;
- journal   : journalisation exhaustive de tous les runs.
"""

__all__ = ["params", "substrate", "seeds", "controls", "measure",
           "runner", "journal"]
