"""Client for the persistent local Decider service."""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict

import requests


DEFAULT_URL = "http://127.0.0.1:18766/v1/systemone"
DEFAULT_CONTAINER_URL = DEFAULT_URL.replace("127.0.0.1", "host.docker.internal")


class DeciderHTTPClient:
    """Expose the official Decider ``system_one`` shape over HTTP."""

    def __init__(self, url: str = DEFAULT_URL, timeout: float = 300.0) -> None:
        self.url = str(url)
        self.timeout = float(timeout)

    def system_one(self, state: Any, questions: Dict[str, Any]) -> Dict[str, Any]:
        response = requests.post(
            self.url,
            json={"state": state, "questions": questions},
            timeout=self.timeout,
        )
        if not response.ok:
            raise RuntimeError(
                f"Decider HTTP {response.status_code}: {response.text}"
            )
        result = response.json()
        if not isinstance(result, dict):
            raise RuntimeError("Decider returned a non-object JSON response")
        return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--timeout", type=float, default=300.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    client = DeciderHTTPClient(args.url, args.timeout)
    result = client.system_one(
        "Task: edit a workbook. Current subgoal: modify the existing chart title.",
        {
            "use_chart_fact": {
                "type": "noul",
                "instructions": (
                    "Should this fact be included? "
                    "Fact: object:chart_1 = chart using Revenue!B2:C10"
                ),
                "criteria": {
                    "true": "The fact is useful for the current subgoal.",
                    "false": "The fact is not useful for the current subgoal.",
                },
            }
        },
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
