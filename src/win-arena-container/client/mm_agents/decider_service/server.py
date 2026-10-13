"""FastAPI service that keeps one local Decider model resident."""

from __future__ import annotations

import asyncio
import gc
import inspect
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


def _optional_fraction(name: str) -> float | None:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return None
    try:
        value = float(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be a number greater than 0 and at most 1") from exc
    if not 0 < value <= 1:
        raise RuntimeError(f"{name} must be greater than 0 and at most 1")
    return value


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    raise RuntimeError(f"{name} must be one of: 1, 0, true, false, yes, no, on, off")


CUDA_MEMORY_FRACTION = _optional_fraction("DECIDER_CUDA_MEMORY_FRACTION")
USE_GRAPHS = _env_bool("DECIDER_USE_GRAPHS", True)


def _patch_decider_conv_keyword_compat() -> bool:
    """Adapt decider-ai 1.9.0's CUDA conv patch to Transformers 5.8.

    Decider's replacement names its first argument ``hidden_states`` while
    Qwen3.5 now calls the function with ``x=...``.  The replacement accepts
    arbitrary extra keywords, so ``x`` is otherwise swallowed and Python then
    reports that ``hidden_states`` is missing.
    """
    import decider.engine as decider_engine

    original = decider_engine.fused_causal_conv1d_fn
    parameters = inspect.signature(original).parameters
    if "x" in parameters or "hidden_states" not in parameters:
        return False

    def fused_causal_conv1d_compat(x, weight, bias=None, activation=None, **kwargs):
        return original(x, weight, bias=bias, activation=activation, **kwargs)

    decider_engine.fused_causal_conv1d_fn = fused_causal_conv1d_compat
    return True


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
        self.cuda_memory_fraction = CUDA_MEMORY_FRACTION
        self.use_graphs = USE_GRAPHS and requested_device.startswith("cuda")
        self.conv_compat_patched = False
        if requested_device.startswith("cuda"):
            if CUDA_MEMORY_FRACTION is not None:
                torch.cuda.set_per_process_memory_fraction(
                    CUDA_MEMORY_FRACTION,
                    device=torch.device(requested_device),
                )
                logging.info(
                    "Limited the CUDA caching allocator to %.1f%% of device memory",
                    CUDA_MEMORY_FRACTION * 100,
                )
            self.conv_compat_patched = _patch_decider_conv_keyword_compat()
            if self.conv_compat_patched:
                logging.info("Applied decider-ai/Transformers causal-conv keyword compatibility patch")
        try:
            self.model = Decider(
                str(self.model_path),
                device=requested_device,
                # Keep Decider's CUDA engine so system_one can use its bounded
                # shared-prefix path even when graph capture is disabled.
                use_graphs=requested_device.startswith("cuda"),
            )
            if requested_device.startswith("cuda") and not self.use_graphs:
                self.model.eng.use_graphs = False
                logging.info("Disabled retained CUDA graph capture")
        except torch.OutOfMemoryError:
            if DEVICE_SETTING != "auto" or requested_device == "cpu":
                raise
            logging.warning("CUDA is out of memory; falling back to CPU inference")
            gc.collect()
            torch.cuda.empty_cache()
            self.device = "cpu"
            self.use_graphs = False
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
        "cuda_memory_fraction": service.cuda_memory_fraction,
        "use_graphs": service.use_graphs,
        "conv_compat_patched": service.conv_compat_patched,
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
