"""FastAPI service that keeps one local Decider model resident."""

from __future__ import annotations

import asyncio
import gc
import logging
import os
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict

# Transformers may select Triton-backed kernels merely because CUDA is
# visible, even when the model is explicitly placed on CPU. Hide CUDA before
# importing torch for a deterministic CPU service.
DEVICE_SETTING = os.environ.get("DECIDER_DEVICE", "auto").strip().lower()
if DEVICE_SETTING == "cpu":
    os.environ["CUDA_VISIBLE_DEVICES"] = ""

import torch
from fastapi import FastAPI, HTTPException, Request


DEFAULT_MODEL_PATH = Path("/home/weimingli/models/decider-2b")
MODEL_PATH = Path(os.environ.get("DECIDER_MODEL", DEFAULT_MODEL_PATH)).expanduser()
MIN_CUDA_FREE_BYTES = int(os.environ.get("DECIDER_MIN_CUDA_FREE_BYTES", 5 * 1024**3))


class DeciderService:
    def __init__(self, model_path: Path) -> None:
        if not model_path.is_dir():
            raise FileNotFoundError(f"Decider model directory not found: {model_path}")
        if DEVICE_SETTING not in {"auto", "cpu", "cuda"} and not DEVICE_SETTING.startswith("cuda:"):
            raise RuntimeError("DECIDER_DEVICE must be auto, cpu, cuda, or cuda:<index>")
        if DEVICE_SETTING.startswith("cuda") and not torch.cuda.is_available():
            raise RuntimeError(f"DECIDER_DEVICE={DEVICE_SETTING}, but CUDA is not available")

        from decider.infer import Decider

        self.model_path = model_path.resolve()
        requested_device = (
            "cuda" if DEVICE_SETTING == "auto" and torch.cuda.is_available()
            else "cpu" if DEVICE_SETTING == "auto"
            else DEVICE_SETTING
        )
        if requested_device == "cuda" and DEVICE_SETTING == "auto":
            free_bytes, _ = torch.cuda.mem_get_info()
            if free_bytes < MIN_CUDA_FREE_BYTES:
                logging.warning(
                    "Only %.2f GiB CUDA memory is free; using CPU (minimum %.2f GiB)",
                    free_bytes / 1024**3,
                    MIN_CUDA_FREE_BYTES / 1024**3,
                )
                requested_device = "cpu"
        self.lock = threading.Lock()
        self.device = requested_device
        try:
            self.model = Decider(str(self.model_path), device=requested_device)
        except torch.OutOfMemoryError:
            if DEVICE_SETTING != "auto" or requested_device == "cpu":
                raise
            logging.warning("CUDA is out of memory; falling back to CPU inference")
            gc.collect()
            torch.cuda.empty_cache()
            self.device = "cpu"
            self.model = Decider(str(self.model_path), device="cpu")

    def system_one(self, state: Any, questions: Dict[str, Any]) -> Dict[str, Any]:
        # One resident model is intentionally serialized to bound GPU memory and
        # avoid concurrent mutation of inference-engine caches.
        with self.lock:
            result = self.model.system_one(state, questions)
        if not isinstance(result, dict):
            raise RuntimeError("Decider returned a non-object result")
        return result


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.decider = await asyncio.to_thread(DeciderService, MODEL_PATH)
    yield
    del app.state.decider


app = FastAPI(title="Local Decider system_one service", version="1.0.0", lifespan=lifespan)


@app.get("/healthz")
def health(request: Request) -> Dict[str, Any]:
    service: DeciderService = request.app.state.decider
    return {
        "status": "ok",
        "model": str(service.model_path),
        "device": service.device,
        "cuda_available": torch.cuda.is_available(),
    }


@app.post("/v1/systemone")
async def system_one(request: Request) -> Dict[str, Any]:
    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Request body must be JSON") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Request body must be a JSON object")
    if "state" not in payload:
        raise HTTPException(status_code=400, detail="Missing state")
    questions = payload.get("questions")
    if not isinstance(questions, dict) or not questions:
        raise HTTPException(status_code=400, detail="questions must be a non-empty object")

    service: DeciderService = request.app.state.decider
    try:
        return await asyncio.to_thread(service.system_one, payload["state"], questions)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logging.exception("Decider inference failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
