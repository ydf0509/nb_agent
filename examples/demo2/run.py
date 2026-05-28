"""
最小 TUI 示例 — 只需 4 行核心代码

完整版示例请参考 nb_agent_bfzs 项目。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import tools  # noqa: F401, E402

from nb_agent import load_config, AgentApp  # noqa: E402

config = load_config()
AgentApp(config).run()
