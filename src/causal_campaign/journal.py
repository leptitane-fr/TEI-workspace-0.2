"""Journal exhaustif des runs — TOUS les runs, y compris ratés (aucune sélection).

Chaque run (réussi, éteint, explosé, avorté) est consigné en JSONL (machine)
et en Markdown (humain), en append-only. Le journal est un instrument
d'expérimentateur : il n'est jamais lu par la dynamique.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

JOURNAL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "journal")
JSONL_PATH = os.path.join(JOURNAL_DIR, "RUNS.jsonl")
MD_PATH = os.path.join(JOURNAL_DIR, "RUNS.md")

_MD_HEADER = (
    "# Journal exhaustif des runs\n\n"
    "Tous les runs sont consignés, y compris les ratés (extinctions, explosions,\n"
    "abandons) — aucune sélection. Détails machine : `RUNS.jsonl` ; données brutes :\n"
    "`data/<run_id>.json`.\n\n"
    "| horodatage (UTC) | run_id | label | statut | ticks | événements | vol final | note |\n"
    "|---|---|---|---|---|---|---|---|\n"
)


def append(run_id: str, label: str, params_dict: dict, status: str,
           ticks: int, n_events: int, n_flight: int, note: str = "") -> None:
    """Consigne un run terminé (quel que soit son sort) dans les deux journaux."""
    os.makedirs(JOURNAL_DIR, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    entry = {"ts": ts, "run_id": run_id, "label": label, "status": status,
             "ticks": ticks, "events": n_events, "flight_final": n_flight,
             "note": note, "params": params_dict}
    with open(JSONL_PATH, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    if not os.path.exists(MD_PATH):
        with open(MD_PATH, "w", encoding="utf-8") as fh:
            fh.write(_MD_HEADER)
    with open(MD_PATH, "a", encoding="utf-8") as fh:
        fh.write(f"| {ts} | `{run_id}` | {label} | **{status}** | {ticks} | "
                 f"{n_events} | {n_flight} | {note} |\n")
