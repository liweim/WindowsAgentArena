import json
import logging
import os
from typing import Any, Dict

logger = logging.getLogger("desktopenv.getters.thunderbird")


def get_thunderbird_drafts(env, config: Dict[str, Any]):
    """Fetch Drafts mbox files from legacy and standard Thunderbird profiles."""
    script = r'''
import glob
import json
import os

appdata = os.environ.get("APPDATA", r"C:\Users\Docker\AppData\Roaming")
patterns = [
    os.path.join(appdata, ".thunderbird", "*", "Mail", "Local Folders", "Drafts"),
    os.path.join(appdata, "Thunderbird", "Profiles", "*", "Mail", "Local Folders", "Drafts"),
]
paths = []
for pattern in patterns:
    for path in glob.glob(pattern):
        if os.path.isfile(path) and path not in paths:
            paths.append(path)
print(json.dumps(paths))
'''
    try:
        output = env.controller.execute_python_command(script)["output"].strip()
        paths = json.loads(output) if output else []
    except Exception as exc:
        logger.error("Error locating Thunderbird drafts: %s", exc)
        return []

    local_paths = []
    for index, path in enumerate(paths):
        try:
            content = env.controller.get_file(path)
            if content is None:
                continue
            local_path = os.path.join(env.cache_dir, f"thunderbird-drafts-{index}.mbox")
            with open(local_path, "wb") as file:
                file.write(content)
            local_paths.append(local_path)
        except Exception as exc:
            logger.warning("Failed to fetch Thunderbird draft file %s: %s", path, exc)
    return local_paths


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
appdata = os.environ.get("APPDATA", r"C:\Users\Docker\AppData\Roaming")
profile_candidates = [profile]
# Thunderbird may migrate/use its standard profile location even when setup
# launches it with the legacy `.thunderbird` profile. Search both locations so
# events visible in the UI are evaluated instead of silently returning [].
profile_candidates.extend(glob.glob(os.path.join(appdata, "Thunderbird", "Profiles", "*")))
profile_candidates.extend(glob.glob(os.path.join(appdata, ".thunderbird", "*")))

db_candidates = []
for candidate in profile_candidates:
    db_candidates.append(os.path.join(candidate, "calendar-data", "local.sqlite"))
    db_candidates.extend(
        glob.glob(os.path.join(candidate, "**", "local.sqlite"), recursive=True)
    )

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
