"""nb_agent — Handwritten ReAct Agent with TUI"""

__version__ = "0.1.0"

from nb_agent.config import load_config
from nb_agent.tui.app import AgentApp

__all__ = ["load_config", "AgentApp", "__version__"]
