"""Send one audio file to the local Parakeet transcription service."""

from __future__ import annotations

import argparse
import json
import mimetypes
from pathlib import Path

import requests


DEFAULT_URL = "http://127.0.0.1:18765/v1/audio/transcriptions"


DEFAULT_AUDIO = Path(
    "/home/weimingli/projects/WindowsAgentArena/src/win-arena-container/client/"
    "evaluation_examples_windows/examples/hearing/assets/"
    "communication-community_class_registration.mp3"
)


def transcribe_audio(
    audio_path: Path | str,
    *,
    url: str = DEFAULT_URL,
    timestamps: bool = False,
    timeout: float = 300.0,
) -> dict:
    """Upload one local audio file and return the Parakeet JSON response."""
    resolved_path = Path(audio_path).expanduser().resolve()
    if not resolved_path.is_file():
        raise FileNotFoundError(f"Audio file not found: {resolved_path}")

    content_type = mimetypes.guess_type(resolved_path.name)[0] or "application/octet-stream"
    with resolved_path.open("rb") as audio_file:
        response = requests.post(
            url,
            files={"file": (resolved_path.name, audio_file, content_type)},
            data={"timestamps": str(timestamps).lower()},
            timeout=timeout,
        )

    if not response.ok:
        raise RuntimeError(f"Parakeet HTTP {response.status_code}: {response.text}")
    result = response.json()
    if not isinstance(result, dict):
        raise RuntimeError("Parakeet returned a non-object JSON response")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", nargs="?", type=Path, default=DEFAULT_AUDIO)
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help="Parakeet transcription endpoint",
    )
    parser.add_argument("--timestamps", action="store_true")
    parser.add_argument("--timeout", type=float, default=300.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        result = transcribe_audio(
            args.audio,
            url=args.url,
            timestamps=args.timestamps,
            timeout=args.timeout,
        )
    except (FileNotFoundError, RuntimeError, requests.RequestException) as exc:
        raise SystemExit(str(exc)) from exc
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
