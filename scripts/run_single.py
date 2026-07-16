#!/usr/bin/env python3
"""Run unique — usage : python3 scripts/run_single.py [clé=valeur ...]

Exemples :
    python3 scripts/run_single.py
    python3 scripts/run_single.py m=64 s=20 seed_name=vee max_ticks=1000 label=essai
Toute clé de Params est acceptée ; label= nomme le run dans le journal.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from causal_campaign.params import Params
from causal_campaign.runner import run, summarize


def main() -> None:
    kwargs = {}
    label = "single"
    for arg in sys.argv[1:]:
        key, _, val = arg.partition("=")
        if key == "label":
            label = val
            continue
        field_type = Params.__dataclass_fields__[key].type
        if field_type == "bool" or isinstance(getattr(Params(), key), bool):
            kwargs[key] = val.lower() in ("1", "true", "yes")
        elif isinstance(getattr(Params(), key), int):
            kwargs[key] = int(val)
        else:
            kwargs[key] = val
    params = Params(**kwargs)
    result = run(params, label)
    print(summarize(result))


if __name__ == "__main__":
    main()
