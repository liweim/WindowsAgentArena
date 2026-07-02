import json
import logging
from typing import Any, Dict

logger = logging.getLogger("desktopenv.getters.thunderbird")


def get_thunderbird_calendar_events(env, config: Dict[str, Any]):
    """
    Read Thunderbird local calendar events from the VM.

    Returns a JSON-like dict containing the VM's current date and rows from
    calendar tables. The metric handles Thunderbird schema differences.
    """
    profile_path = config.get(
        "profile_path",
        r"C:\Users\Docker\AppData\Roaming\.thunderbird\t5q2a5hp.default-release",
    )

    script = rf'''
import datetime
import glob
import json
import os
import sqlite3

profile = r"{profile_path}"
db_candidates = [
    os.path.join(profile, "calendar-data", "local.sqlite"),
]
db_candidates.extend(glob.glob(os.path.join(profile, "**", "local.sqlite"), recursive=True))

result = {{
    "today": datetime.date.today().isoformat(),
    "events": [],
    "db_paths": [],
}}

for db_path in db_candidates:
    if not os.path.exists(db_path) or db_path in result["db_paths"]:
        continue
    result["db_paths"].append(db_path)
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        tables = [
            row[0] for row in cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            if row[0].lower().startswith("cal_")
        ]
        event_rows = []
        related_rows = []
        for table in tables:
            try:
                rows = cur.execute(f"SELECT * FROM {{table}}").fetchall()
            except Exception:
                continue
            for row in rows:
                item = {{"table": table}}
                item.update({{key: row[key] for key in row.keys()}})
                if "event" in table.lower():
                    event_rows.append(item)
                else:
                    related_rows.append(item)
        for event in event_rows:
            event_id = event.get("id")
            event["related"] = [
                row for row in related_rows
                if event_id is not None and event_id in [
                    row.get("item_id"),
                    row.get("event_id"),
                    row.get("id"),
                    row.get("cal_id"),
                ]
            ]
            result["events"].append(event)
        conn.close()
    except Exception as exc:
        result.setdefault("errors", []).append(f"{{db_path}}: {{exc}}")

print(json.dumps(result, default=str))
'''

    try:
        output = env.controller.execute_python_command(script)["output"].strip()
        return json.loads(output) if output else {"events": []}
    except Exception as exc:
        logger.error("Error reading Thunderbird calendar events: %s", exc)
        return {"events": []}
