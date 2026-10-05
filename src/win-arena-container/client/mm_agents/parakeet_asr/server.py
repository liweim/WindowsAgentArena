"""FastAPI service for the local NVIDIA Parakeet NeMo checkpoint."""

from __future__ import annotations

import asyncio
import logging
import os
import tempfile
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import torch
import soundfile as sf
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from scipy.signal import resample_poly


DEFAULT_MODEL_PATH = Path(
    "/home/weimingli/models/parakeet-tdt-0.6b-v2/parakeet-tdt-0.6b-v2.nemo"
)
MODEL_PATH = Path(os.environ.get("PARAKEET_MODEL", DEFAULT_MODEL_PATH)).expanduser()
DEVICE_SETTING = os.environ.get("PARAKEET_DEVICE", "auto").lower()
MAX_UPLOAD_BYTES = int(os.environ.get("PARAKEET_MAX_UPLOAD_BYTES", 500 * 1024 * 1024))
ALLOWED_SUFFIXES = {".flac", ".mp3", ".ogg", ".wav"}


def _select_device() -> torch.device:
    if DEVICE_SETTING == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if DEVICE_SETTING == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("PARAKEET_DEVICE=cuda, but CUDA is not available")
    if DEVICE_SETTING not in {"cpu", "cuda"}:
        raise RuntimeError("PARAKEET_DEVICE must be auto, cpu, or cuda")
    return torch.device(DEVICE_SETTING)


def _jsonable(value: Any) -> Any:
    """Convert timestamp values, including NumPy scalars, to JSON-safe objects."""
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if hasattr(value, "item"):
        try:
            return value.item()
        except (TypeError, ValueError):
            pass
    return value


class ParakeetService:
    def __init__(self, model_path: Path) -> None:
        if not model_path.is_file():
            raise FileNotFoundError(f"Parakeet checkpoint not found: {model_path}")

        # Importing NeMo is relatively slow, so keep it out of lightweight client code.
        import nemo.collections.asr as nemo_asr

        requested_device = _select_device()
        self.model_path = model_path.resolve()
        self.lock = threading.Lock()
        # Restore on CPU first so "auto" can recover cleanly when the GPU is
        # visible but currently has too little free memory.
        self.model = nemo_asr.models.ASRModel.restore_from(
            restore_path=str(self.model_path),
            map_location=torch.device("cpu"),
        )
        self.model.eval()
        self.device = requested_device
        try:
            self.model.to(self.device)
        except torch.OutOfMemoryError:
            if DEVICE_SETTING != "auto":
                raise
            logging.warning("CUDA is out of memory; falling back to CPU inference")
            self.device = torch.device("cpu")
            self.model.to(self.device)
            torch.cuda.empty_cache()
        self.model.freeze()

    def transcribe(self, audio_path: str, timestamps: bool) -> dict[str, Any]:
        normalized_path = self._normalize_audio(audio_path)
        try:
            # A single model instance is serialized to avoid concurrent mutation in
            # NeMo's transcribe data loader and unpredictable GPU memory spikes.
            with self.lock, torch.inference_mode():
                hypothesis = self.model.transcribe(
                    [str(normalized_path)], batch_size=1, timestamps=timestamps
                )[0]
        finally:
            normalized_path.unlink(missing_ok=True)

        text = hypothesis if isinstance(hypothesis, str) else hypothesis.text
        result: dict[str, Any] = {"text": text}
        timestamp_data = getattr(hypothesis, "timestamp", None)
        if timestamps and timestamp_data:
            result["timestamps"] = _jsonable(timestamp_data)
        return result

    @staticmethod
    def _normalize_audio(audio_path: str) -> Path:
        """Decode input and produce an exact 16 kHz mono WAV for NeMo/Lhotse."""
        import math

        audio, sample_rate = sf.read(audio_path, dtype="float32", always_2d=True)
        if audio.size == 0:
            raise ValueError("Audio file is empty")

        mono = audio.mean(axis=1)
        if sample_rate != 16_000:
            common_factor = math.gcd(sample_rate, 16_000)
            mono = resample_poly(
                mono,
                up=16_000 // common_factor,
                down=sample_rate // common_factor,
            )

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as wav_file:
            normalized_path = Path(wav_file.name)
        sf.write(normalized_path, mono, 16_000, subtype="PCM_16")
        return normalized_path


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.parakeet = await asyncio.to_thread(ParakeetService, MODEL_PATH)
    yield
    del app.state.parakeet


app = FastAPI(title="Parakeet TDT 0.6B v2 ASR", version="1.0.0", lifespan=lifespan)


@app.get("/healthz")
def health(request: Request) -> dict[str, Any]:
    service: ParakeetService = request.app.state.parakeet
    return {
        "status": "ok",
        "model": str(service.model_path),
        "device": str(service.device),
        "cuda_available": torch.cuda.is_available(),
    }


@app.post("/v1/audio/transcriptions")
async def transcribe(
    request: Request,
    file: UploadFile = File(...),
    timestamps: bool = Form(False),
) -> dict[str, Any]:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        allowed = ", ".join(sorted(ALLOWED_SUFFIXES))
        raise HTTPException(status_code=400, detail=f"Supported formats: {allowed}")

    temp_path: Path | None = None
    try:
        total = 0
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            while chunk := await file.read(1024 * 1024):
                total += len(chunk)
                if total > MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail="Audio upload is too large")
                temp_file.write(chunk)

        service: ParakeetService = request.app.state.parakeet
        return await asyncio.to_thread(service.transcribe, str(temp_path), timestamps)
    finally:
        await file.close()
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
