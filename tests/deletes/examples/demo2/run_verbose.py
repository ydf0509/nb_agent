"""
详细版入口 — 启动前打印所有加载信息

和 run.py 功能相同，额外打印已注册工具、Skills、MCP 状态。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import tools  # noqa: F401, E402

from pathlib import Path  # noqa: E402
from nb_agent.config import load_config  # noqa: E402
from nb_agent.core.models import load_models_from_config  # noqa: E402
from nb_agent.skills import SkillManager  # noqa: E402
from nb_agent.tools import TOOL_REGISTRY  # noqa: E402
from nb_agent.tui.app import AgentApp  # noqa: E402

config = load_config()

print("=" * 50)
print("  nb_agent TUI Demo")
print("=" * 50)

models = load_models_from_config(config)
print(f"\n模型: {len(models)} 个可用")
for m in models:
    default_mark = " <-- 默认" if m.id == config["agent"]["default_model"] else ""
    print(f"  {m.name}{default_mark}")

print(f"\n工具: {len(TOOL_REGISTRY)} 个已注册")
for name in TOOL_REGISTRY:
    print(f"  - {name}")

mgr = SkillManager(project_root=Path.cwd())
mgr.discover()
skills = mgr.get_all_skills()
print(f"\nSkills: {len(skills)} 个已发现")
for s in skills:
    tag = " [仅手动]" if s["manual_only"] else ""
    print(f"  - {s['name']}{tag}")

mcp_cfg = config.get("mcp", {})
mcp_enabled = [name for name, cfg in mcp_cfg.items() if cfg.get("enabled", True)]
print(f"\nMCP Servers: {len(mcp_enabled)} 个已启用")
for name in mcp_enabled:
    print(f"  - {name}")

print("\n启动 TUI...\n")
AgentApp(config).run()
