"""TARS multi-agent system for WindowsAgentArena."""

# Load model clients only when starting a task; local inference needs no cloud keys.
from .main import TARS

__all__ = ["TARS"]
