"""Send one audio file to the local Parakeet transcription service."""

from __future__ import annotations

import argparse
import json
import mimetypes
from pathlib import Path

import requests


DEFAULT_AUDIO = Path(
    "/home/weimingli/projects/WindowsAgentArena/src/win-arena-container/client/"
    "evaluation_examples_windows/examples/hearing/assets/"
    "communication-community_class_registration.mp3"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", nargs="?", type=Path, default=DEFAULT_AUDIO)
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:18765/v1/audio/transcriptions",
        help="Parakeet transcription endpoint",
    )
    parser.add_argument("--timestamps", action="store_true")
    parser.add_argument("--timeout", type=float, default=300.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    audio_path = args.audio.expanduser().resolve()
    if not audio_path.is_file():
        raise SystemExit(f"Audio file not found: {audio_path}")

    content_type = mimetypes.guess_type(audio_path.name)[0] or "application/octet-stream"
    with audio_path.open("rb") as audio_file:
        response = requests.post(
            args.url,
            files={"file": (audio_path.name, audio_file, content_type)},
            data={"timestamps": str(args.timestamps).lower()},
            timeout=args.timeout,
        )

    if not response.ok:
        raise SystemExit(f"HTTP {response.status_code}: {response.text}")
    print(json.dumps(response.json(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
