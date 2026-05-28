"""工具模块 — 导入所有工具以触发 @tool 注册，导出 TOOL_REGISTRY"""

from .base import TOOL_REGISTRY, tool  # noqa: F401

import nb_agent.tools.builtin  # noqa: F401
