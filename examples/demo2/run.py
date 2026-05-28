"""
智能笔记助手 — 用户只需写这几行代码即可启动 nb_agent TUI

步骤:
  1. 在 tools/ 目录下用 @tool 定义工具
  2. 在 .nb_agent/skills/ 下放 SKILL.md
  3. 在 config.jsonc 里配置模型和 MCP
  4. python run.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import tools  # noqa: F401, E402  导入即注册自定义工具

from nb_agent.config import load_config  # noqa: E402
from nb_agent.tui.app import AgentApp   # noqa: E402

config = load_config()
config["_project_root"] = os.getcwd()
AgentApp(config).run()
