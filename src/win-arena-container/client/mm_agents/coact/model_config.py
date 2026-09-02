from __future__ import annotations

from mm_agents.llm import LOCAL_API_URL, MODEL_CONFIGS, UITARS_API_URL
from .autogen.llm_config import LLMConfig
from mm_agents.utils import get_price


def is_local_model(model_name: str) -> bool:
    return model_name in MODEL_CONFIGS and MODEL_CONFIGS[model_name].client_class == "LocalLLM"


def get_local_base_url(model_name: str) -> str:
    if model_name == "uitars-1.5-7b":
        return UITARS_API_URL
    return LOCAL_API_URL


def build_llm_config(model_name: str, config_path: str | None = None) -> LLMConfig:
    if is_local_model(model_name):
        return LLMConfig(
            api_type="openai",
            model=model_name,
            base_url=get_local_base_url(model_name),
            api_key="empty",
        )

    if not config_path:
        return LLMConfig(api_type="openai", model=model_name)

    return LLMConfig.from_json(path=config_path).where(model=model_name)


def make_usage_entry(
    model_name: str,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    image_count: int = 0,
) -> dict:
    prompt_price, completion_price = get_price(model_name)
    return {
        "model_name": model_name,
        "cost": prompt_tokens * prompt_price + completion_tokens * completion_price,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "image_count": image_count,
    }


def extract_autogen_usage(agent, model_name: str, image_count: int = 0) -> dict:
    usage = {}
    if agent is not None and hasattr(agent, "get_total_usage"):
        total_usage = agent.get_total_usage() or {}
        usage = total_usage.get(model_name, {}) or {}
    return make_usage_entry(
        model_name=model_name,
        prompt_tokens=usage.get("prompt_tokens", 0),
        completion_tokens=usage.get("completion_tokens", 0),
        image_count=image_count,
    )


def add_usage_entry(target: dict, key: str, entry: dict) -> None:
    if key not in target:
        target[key] = make_usage_entry(entry["model_name"])

    target[key]["cost"] += entry.get("cost", 0.0)
    target[key]["prompt_tokens"] += entry.get("prompt_tokens", 0)
    target[key]["completion_tokens"] += entry.get("completion_tokens", 0)
    target[key]["image_count"] += entry.get("image_count", 0)


def summarize_usage_entries(model_usage: dict) -> dict:
    prompt_tokens = sum(stats["prompt_tokens"] for stats in model_usage.values())
    completion_tokens = sum(stats["completion_tokens"] for stats in model_usage.values())
    image_count = sum(stats["image_count"] for stats in model_usage.values())
    total_cost = sum(stats["cost"] for stats in model_usage.values())
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "image_count": image_count,
        "total_cost": total_cost,
    }
