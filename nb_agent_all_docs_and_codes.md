
# 🤖 AI 上下文阅读协议 (由 nb_ai_context 生成)

> **此文档生成时间**：2026-05-27 19:59:46
> **系统指令**：你正在解析一份由工具 **`nb_ai_context`** 自动生成的**结构化项目快照**。
> **文档性质**：这**不是**一份普通的面向人类的文档，而是专为 AI 大模型（LLM）设计的上下文数据流。它将项目文档、源代码和 AST 架构元数据进行了特殊的结构化合并，请开启"代码解析器"的心智模式。


## 🧠 AI 认知与解析准则

这份由 `nb_ai_context` 生成的文档是你的核心知识库。其中的内容是动态的——它可能包含完整的底层源码，也可能仅包含使用教程，或者是两者的混合。请严格遵循以下自适应阅读策略：

### 1. 信息的层级与冲突处理
*   **文档即意图**：将 `README`、教程文档和 Docstrings 视为项目设计的**最高意图**。如果生成器省略了对应源码，请完全信任文档逻辑，以此为基础推理。
*   **源码即事实**：遇到 `.py` 源码或 AST 元数据（类/函数签名）时，以此作为实现细节、类型约束和语法准确性的**最终事实标准**。
*   **冲突处理**：若文档与源码/AST 存在矛盾，请以源码为准，并在回答中向用户简要指出该差异。
*   **测试代码的忽略**：为优化 Token 长度，集成/单元测试及非核心 API 源码通常被隐藏。**绝对不要**因此推断或提醒用户“项目缺乏测试”或“代码未实现”。

### 2. 文件边界与架构感知
*   **上下文定界**：工具使用 `--- **start of file: <路径>** ---` 等标记严格界定文件。**在你的回复中，请使用标准 Markdown 代码块，切勿模仿使用此类系统定界符。**
*   **结构可视化**：利用“文件树 (File Tree)”章节建立项目的宏观架构认知。
*   **依赖关系**：利用“文件依赖分析”章节理清模块间的 import 数据流向。

### 3. 严格的代码生成与交互边界
*   **事实锚定 (Fact Anchoring)**：你生成的代码必须严格锚定在本文档范围内！API 调用必须基于**源码中的 AST 签名**或**文档中的演示示例**。
*   **严禁臆造 (Zero Fabrication)**：绝对禁止编造文档中未定义或未提及的类名、方法名或参数。
*   **越界拒绝**：如果用户询问的功能在当前提供的上下文中完全不存在，请明确告知“当前上下文中未包含该信息”，而不是试图凭空生成。

---
# markdown content namespace: nb_agent project summary 



- `nb_agent` 是一个可 import 使用的 TUI Agent 框架，让用户快速开发自己的 AI Agent 项目。
- 三种扩展机制：Tools（@tool 装饰器）、MCP（外部 MCP Server）、Skills（SKILL.md 文档注入）
- 核心模块：
  - `nb_agent/core/agent.py`: AgentCore — 对话循环、工具调用、模型切换、分组管理
  - `nb_agent/tools/base.py`: @tool 装饰器 — 自动生成 OpenAI Function Calling schema，支持 group 参数
  - `nb_agent/mcp/manager.py`: MCP 管理器 — 动态连接 MCP Server、工具发现
  - `nb_agent/skills/manager.py`: SkillManager — SKILL.md 发现、加载、匹配
  - `nb_agent/tui/app.py`: TUI 界面 — 基于 Textual 的终端交互（F2 Skills / F3 工具组 / @ 补全）
  - `nb_agent/session/store.py`: 会话持久化 — SQLModel + SQLite
  - `nb_agent/approval/`: 危险操作审批机制
  - `nb_agent/config/`: 配置管理（JSONC 格式）
- 用户用法：`from nb_agent.core import AgentCore` + `from nb_agent.tools import tool`
- 支持工具分组（tool_group）：`@tool(group="file")` → `file__read_file`，TUI 中可禁用整组


## 📋 nb_agent most core source files metadata (Entry Points)


以下是项目 nb_agent 最核心的入口文件的结构化元数据，帮助快速理解项目架构：



### the project nb_agent most core source code files as follows: 
- `nb_agent/core/agent.py`
- `nb_agent/tools/base.py`
- `nb_agent/tui/app.py`


### 📄 Python File Metadata: `nb_agent/core/agent.py`

#### 📝 Module Docstring

`````
AgentCore — ReAct 循环核心

核心循环：
  用户输入 → LLM(messages + tools) → 判断:
    有 tool_calls → 执行工具 → 结果回传 LLM → 再次判断（可能多轮）
    无 tool_calls → 返回文本回复
`````

#### 📦 Imports

- `import asyncio`
- `import functools`
- `import json`
- `import uuid`
- `from typing import AsyncIterator`
- `from typing import List`
- `from typing import Dict`
- `from typing import Optional`
- `from typing import Callable`
- `from openai import AsyncOpenAI`
- `from nb_agent.core.models import ModelInfo`
- `from nb_agent.core.models import ToolCallRecord`
- `from nb_agent.core.models import AgentResponse`
- `from nb_agent.core.models import load_models_from_config`
- `from nb_agent.core.context import trim_context`
- `from nb_agent.core.retry import call_llm_with_retry`
- `from nb_agent.core.retry import RETRYABLE_ERRORS`
- `from nb_agent.core.retry import MAX_RETRIES`
- `from nb_agent.session import SessionStore`
- `from nb_agent.mcp import MCPManager`
- `from nb_agent.approval import ApprovalEngine`
- `from nb_agent.tools import TOOL_REGISTRY`
- `from nb_agent.skills import SkillManager`

#### 🏛️ Classes (1)

##### 📌 `class AgentCore`
*Line: 30*

**Docstring:**
`````
Agent 核心：
- Function Calling：LLM 自主决定是否调用工具
- 多轮工具调用：一次对话中可调用多个工具、多轮
- 通过回调实时通知 TUI 工具调用状态
`````

**🔧 Constructor (`__init__`):**
- `def __init__(self, config: dict)`
  - **Parameters:**
    - `self`
    - `config: dict`

**Public Methods (18):**
- `async def chat(self, user_input: str) -> AgentResponse`
- `async def chat_stream(self, user_input: str) -> AsyncIterator[str]`
  - *工具调用阶段用非流式（需要完整 tool_calls），最终回复用流式输出*
- `async def connect_mcp(self)`
- `async def disconnect_mcp(self)`
- `def switch_model(self, model_id: str) -> bool`
- `def get_models_grouped(self) -> Dict[str, List[ModelInfo]]`
- `async def generate_smart_title(self)`
- `def clear_history(self)`
- `def get_session_list(self, limit: int = 50) -> list`
- `def get_tools(self) -> list`
- `def get_tool_groups(self) -> list`
  - *返回所有工具分组及其状态*
- `def toggle_tool_group(self, group: str) -> bool`
  - *切换工具分组的启用/禁用状态，返回 True=已启用*
- `def get_mcp_status(self) -> list`
- `def toggle_mcp_server(self, name: str) -> bool`
- `def get_model_name(self) -> str`
- `def get_model_display_name(self) -> str`
- `def get_token_usage(self) -> dict`
- `def register_tool(self, name: str, func: Callable, description: str, parameters: dict, group: str = '')`

**Class Variables (1):**
- `MAX_TOOL_ROUNDS = 30`


---




### 📄 Python File Metadata: `nb_agent/tools/base.py`

#### 📝 Module Docstring

`````
工具注册框架 — 基于 Pydantic + 装饰器自动生成 OpenAI Function Calling Schema

用法:
    from nb_agent.tools import tool

    class MyParams(BaseModel):
        query: str = Field(description="搜索关键词")

    # 无分组
    @tool
    def search(params: MyParams) -> str:
        """搜索互联网"""
        ...

    # 有分组 — 注册名变为 file__read_file
    @tool(group="file")
    def read_file(params: ReadParams) -> str:
        """读取文件"""
        ...
`````

#### 📦 Imports

- `import inspect`
- `from typing import Dict`
- `from typing import Callable`
- `from typing import Optional`
- `from typing import Type`
- `from typing import get_type_hints`
- `from pydantic import BaseModel`

#### 🔧 Public Functions (2)

- `def tool(func = None)`
  - *Line: 131*
  - **Docstring:**
  `````
  装饰器：自动注册工具函数到 TOOL_REGISTRY
  
  用法:
      @tool                          # 无分组，注册名 = func_name
      @tool(group="file")            # 有分组，注册名 = file__func_name
  `````

- `def decorator(fn)`
  - *Line: 140*


---




### 📄 Python File Metadata: `nb_agent/tui/app.py`

#### 📝 Module Docstring

`````
TUI 界面 —— 用 Textual 框架构建

布局:
┌─────────────────────────────────────────────────┐
│  nb_agent | deepseek-v4-flash | Tokens: 0       │  ← Header
├──────────────────────────────┬──────────────────-┤
│                              │  已注册工具:      │
│  对话区域（滚动）             │  - get_time      │  ← Main
│                              │  - calculate     │
│  user: 你好                  │                  │
│  model: [流式输出中...]       │  MCP: 未连接      │
│                              │                  │
├──────────────────────────────┴──────────────────-┤
│  > 输入消息...                          [发送]   │  ← Input
│  (Enter=发送, Shift+Enter=换行)                  │
├─────────────────────────────────────────────────┤
│  Tab=模型 | Ctrl+Q=退出 | Ctrl+L=清屏            │  ← Footer
└─────────────────────────────────────────────────┘
`````

#### 📦 Imports

- `import asyncio`
- `import os`
- `import re`
- `import sys`
- `import time`
- `from datetime import datetime`
- `from pathlib import Path`
- `from typing import Optional`
- `from textual.app import App`
- `from textual.app import ComposeResult`
- `from textual.containers import Horizontal`
- `from textual.widgets import Footer`
- `from textual.widgets import Header`
- `from textual.widgets import RichLog`
- `from textual.widgets import Static`
- `from textual.binding import Binding`
- `from textual.screen import ModalScreen`
- `from rich.text import Text`
- `from rich.markdown import Markdown as RichMarkdown`
- `from rich.panel import Panel`
- `from nb_agent.core import AgentCore`
- `from widgets import ChatInput`
- `from widgets import ToolPanel`
- `from widgets import ModelSelectScreen`
- `from widgets import HelpScreen`
- `from widgets import SessionSelectScreen`
- `from widgets import ToolDetailScreen`
- `from widgets import RoundsInputScreen`
- `from widgets import ToolApprovalScreen`
- `from widgets import SkillListScreen`
- `from widgets import SkillContentScreen`
- `from widgets import MentionSelectScreen`
- `from widgets import ToolGroupToggleScreen`
- `from widgets import AgentCommands`
- `from widgets.tool_panel import _fmt_tokens`

#### 🏛️ Classes (1)

##### 📌 `class AgentApp(App)`
*Line: 70*

**Docstring:**
`````
nb_agent TUI 主应用
`````

**🔧 Constructor (`__init__`):**
- `def __init__(self, config: dict)`
  - **Parameters:**
    - `self`
    - `config: dict`

**Public Methods (15):**
- `def compose(self) -> ComposeResult`
- `async def on_mount(self)`
- `def action_stop_ai(self)`
- `def action_edit_last(self)`
- `async def action_send_msg(self)`
- `def action_new_session(self)`
- `def action_resume_session(self)`
- `def action_show_help(self)`
- `def action_toggle_input(self)`
- `def action_show_skills(self)`
- `def action_toggle_tool_groups(self)`
- `def on_chat_input_mention_triggered(self, event: ChatInput.MentionTriggered) -> None`
- `def action_clear_chat(self)`
- `def action_select_model(self)`
- `async def on_unmount(self)`

**Class Variables (4):**
- `TITLE = 'nb_agent'`
- `CSS_PATH = 'styles.tcss'`
- `COMMANDS = App.COMMANDS | {AgentCommands}`
- `BINDINGS = [Binding('ctrl+j', 'send_msg', '发送', show=True, priority=True), Binding('ctrl+k', 'stop_ai', '终止', show=True, priority=True), Binding('ctrl+up', 'edit_last', '编辑上轮', show=True, priority=True), Binding('tab', 'select_model', '模型', show=True, priority=True), Binding('ctrl+n', 'new_session', '新建', show=True, priority=True), Binding('ctrl+r', 'resume_session', '恢复', show=True, priority=True), Binding('ctrl+e', 'toggle_input', '展开', show=True, priority=True), Binding('ctrl+l', 'clear_chat', '清屏', show=True), Binding('f1', 'show_help', '帮助', show=True), Binding('f2', 'show_skills', 'Skills', show=True), Binding('f3', 'toggle_tool_groups', '工具组', show=True), Binding('ctrl+q', 'quit', '退出', show=True, priority=True)]`


---



## 🔗 nb_agent Some File Dependencies Analysis

以下是项目文件之间的依赖关系，帮助 AI 理解代码结构：

### 📊 Internal Dependencies Graph

`````
Entry Points (not imported by other project files):
  ★ nb_agent/core/agent.py
  ★ nb_agent/tools/base.py
  ★ nb_agent/tui/app.py

`````

### 📋 Detailed Dependencies

### 📦 Third-party Dependencies

项目使用的第三方库：

- `nb_agent`
- `openai`
- `pydantic`
- `rich`
- `textual`
- ......以及更多的第三方库......


---
# markdown content namespace: nb_agent Project Root Dir Some Files 


## nb_agent File Tree (relative dir: `.`)


`````

├── README.md
└── pyproject.toml

`````

---


## nb_agent (relative dir: `.`)  Included Files (total: 2 files)


- `README.md`

- `pyproject.toml`


---


--- **start of file: README.md** (project: nb_agent) --- 

`````markdown
# nb_agent

**手写 ReAct Agent 框架 + 赛博朋克 TUI** — 不依赖 LangChain，用纯 Python 实现 LLM ↔ Tool 循环。

## 特性

- **手写 ReAct 循环**：LLM → tool_calls → execute → feedback 循环，无框架黑魔法
- **三种扩展方式**：Tools（内置）+ MCP（外部）+ Skills（Markdown 指导手册）
- **MCP 多 Server 管理**：stdio / SSE / HTTP 三传输，运行时启禁，工具命名空间防冲突
- **生产级特性**：上下文裁剪、指数退避重试、危险操作审批、SQLite 会话持久化
- **赛博朋克 TUI**：流式输出 + 思考链 + 模型切换 + MCP 状态 + Token 统计

## 快速开始

```bash
pip install nb_agent
nb_agent
```

## 配置

复制 `config.example.jsonc` 到工作目录，重命名为 `config.jsonc`：

```bash
cp config.example.jsonc config.jsonc
# 编辑 config.jsonc，填入你的 API Key
nb_agent
```

配置优先级：`CLI 参数 > 环境变量 > 项目级 ./config.jsonc > 全局 ~/.nb_agent/config.jsonc > 默认值`

## 三种扩展方式

### Tools — 内置工具

```python
from nb_agent.tools import tool
from pydantic import BaseModel, Field

class MyParams(BaseModel):
    query: str = Field(description="搜索关键词")

@tool
def search(params: MyParams) -> str:
    """搜索互联网"""
    ...
```

### MCP — 外部工具协议

在 `config.jsonc` 中配置：

```jsonc
{
  "mcp": {
    "rag": {
      "command": "uvx",
      "args": ["nb_agentic_rag"],
      "enabled": true
    }
  }
}
```

### Skills — Markdown 指导手册

Skills 教 AI "怎么做"某类任务。与 Tools 不同，Skills 不是可执行代码，而是 **Markdown 格式的指导手册**，教 AI 按最佳实践流程完成特定类型的任务。

**渐进式披露（Progressive Disclosure）**：
- AI 启动时，system prompt 只注入 Skills **清单摘要**（名称+一句描述），不浪费 token
- AI 判断需要某个 Skill 时，调用 `view_skill("code-review")` 工具获取完整指南
- 获取到的 SKILL.md 内容包含详细的执行流程、检查清单、输出模板等

**遵循 agentskills.io 开放标准**（Anthropic 发起，Claude Code / OpenAI Codex / Cursor 等 20+ 平台采纳）。

**目录扫描**（优先级从低到高，同名 Skill 后者覆盖前者）：

```
内置:     随包发布 (code-review, explain-code, refactor)
全局级:   ~/.nb_agent/skills/my-skill/SKILL.md
跨平台:   ~/.agents/skills/my-skill/SKILL.md      ← 与 Codex/Gemini 共享
项目级:   .nb_agent/skills/my-skill/SKILL.md
跨平台:   .agents/skills/my-skill/SKILL.md         ← 与 Codex/Gemini 共享
```

**SKILL.md 格式**（国际标准）：

```markdown
---
name: code-review
description: >-
  审查代码质量、安全性和最佳实践。当用户请求代码审查、
  review PR、检查代码变更时使用。
paths: "**/*.py, **/*.js"
disable-model-invocation: false
---

# 代码审查 Skill

## 审查流程
1. 理解意图：先确认变更要解决什么问题
2. 安全检查：检查输入验证、权限控制...
...
```

**frontmatter 字段说明：**

| 字段 | 必须 | 说明 |
|------|------|------|
| `name` | 是 | kebab-case，max 64 chars，必须匹配目录名 |
| `description` | 是 | max 1024 chars，必须包含 WHAT（做什么）+ WHEN（什么时候用） |
| `paths` | 否 | glob 模式，作用域限定（Cursor 扩展字段） |
| `disable-model-invocation` | 否 | 设为 `true` 时 AI 不会自动调用，只能手动触发 |

**自定义 Skill 示例**：

```bash
mkdir -p .nb_agent/skills/deploy-checklist
```

```markdown
---
name: deploy-checklist
description: >-
  部署前检查清单。当用户提到部署、发布、上线时使用。
---

# 部署检查 Skill

## 检查项
1. 所有测试通过
2. 环境变量已配置
3. 数据库迁移已执行
...
```

重启 nb_agent 后，AI 就能在需要时自动调用这个 Skill。

**跨平台兼容**：放在 `.agents/skills/` 目录下的 Skill 可以同时被 nb_agent、OpenAI Codex、Gemini CLI 等工具识别。

## CLI

```bash
nb_agent                              # 启动 TUI
nb_agent --config ./my_config.jsonc   # 指定配置
nb_agent run "帮我分析代码性能"        # 非交互模式
nb_agent sessions list                # 查看历史会话
```

## TUI 快捷键

| 快捷键 | 功能 |
|--------|------|
| Ctrl+J | 发送消息 |
| Tab    | 切换模型 |
| Ctrl+N | 新建会话 |
| Ctrl+R | 恢复历史会话 |
| Ctrl+K | 终止 AI 回答 |
| Ctrl+P | 命令面板 |
| F1     | 帮助 |

## 架构总览

```
用户输入 → AgentCore (ReAct Loop)
             ├── 内置 Tools (@tool 装饰器)
             ├── MCP Server (外部工具协议)
             └── Skills (view_skill → SKILL.md)
                    ↕
              LLM API (OpenAI 兼容)
                    ↕
              流式/非流式回复 → TUI 渲染
```

**三种扩展方式完全正交**：
- Tools = 可执行的 Python 函数
- MCP = 外部进程提供的工具（通过 stdio/SSE/HTTP 通信）
- Skills = Markdown 格式的指导手册（通过 `view_skill` 工具按需加载）

## 项目结构

```
nb_agent/
├── config/          — 配置加载 (JSONC + ENV)
├── core/            — AgentCore ReAct 循环
│   ├── agent.py     — 核心 Agent 类
│   ├── models.py    — 模型信息 & 数据类
│   ├── context.py   — Token 估算 & 上下文裁剪
│   └── retry.py     — 指数退避重试
├── tools/           — @tool 装饰器 + 内置工具
├── mcp/             — MCP 多 Server 管理
├── skills/          — SKILL.md 指导手册系统
│   ├── manager.py   — SkillManager
│   └── builtin/     — 内置 Skills
├── session/         — SQLModel 会话持久化
├── approval/        — 工具审批引擎
└── tui/             — Textual TUI 界面
    ├── app.py       — AgentApp 主类
    └── widgets/     — 拆分的 UI 组件
        ├── inputs.py      — 输入框组件
        ├── tool_panel.py  — 右侧信息面板
        ├── screens.py     — 弹窗 (模型/会话/帮助/审批...)
        └── commands.py    — 命令面板
```

## License

MIT

`````

--- **end of file: README.md** (project: nb_agent) --- 

---


--- **start of file: pyproject.toml** (project: nb_agent) --- 

`````text
[project]
name = "nb_agent"
version = "0.1.0"
description = "Handwritten ReAct Agent with TUI — Tools + MCP + Skills"
readme = "README.md"
license = "MIT"
requires-python = ">=3.11"
keywords = ["ai-agent", "react-agent", "function-calling", "mcp", "tui", "skills"]

dependencies = [
    "textual>=0.50.0",
    "rich>=13.0.0",
    "json5>=0.9.0",
    "openai>=1.0.0",
    "httpx>=0.24.0",
    "pydantic>=2.0.0",
    "python-dotenv>=1.0.0",
    "mcp>=1.0.0",
    "pyyaml>=6.0",
    "sqlmodel>=0.0.16",
]

[project.optional-dependencies]
dev = ["pytest>=7.0", "pytest-asyncio>=0.20"]

[project.scripts]
nb_agent = "nb_agent.main:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

`````

--- **end of file: pyproject.toml** (project: nb_agent) --- 

---

# markdown content namespace: nb_agent codes 


## nb_agent File Tree (relative dir: `nb_agent`)


`````

└── nb_agent
    ├── __init__.py
    ├── __main__.py
    ├── approval
    │   ├── __init__.py
    │   └── engine.py
    ├── config
    │   ├── __init__.py
    │   └── loader.py
    ├── core
    │   ├── __init__.py
    │   ├── agent.py
    │   ├── context.py
    │   ├── models.py
    │   └── retry.py
    ├── main.py
    ├── mcp
    │   ├── __init__.py
    │   └── client.py
    ├── session
    │   ├── __init__.py
    │   ├── models.py
    │   └── store.py
    ├── skills
    │   ├── __init__.py
    │   ├── builtin
    │   │   ├── code-review
    │   │   │   └── SKILL.md
    │   │   ├── explain-code
    │   │   │   └── SKILL.md
    │   │   └── refactor
    │   │       └── SKILL.md
    │   └── manager.py
    ├── tools
    │   ├── __init__.py
    │   ├── base.py
    │   └── builtin.py
    └── tui
        ├── __init__.py
        ├── app.py
        ├── styles.tcss
        └── widgets
            ├── __init__.py
            ├── commands.py
            ├── inputs.py
            ├── screens.py
            └── tool_panel.py

`````

---


## nb_agent (relative dir: `nb_agent`)  Included Files (total: 33 files)


- `nb_agent/main.py`

- `nb_agent/__init__.py`

- `nb_agent/__main__.py`

- `nb_agent/approval/engine.py`

- `nb_agent/approval/__init__.py`

- `nb_agent/config/loader.py`

- `nb_agent/config/__init__.py`

- `nb_agent/core/agent.py`

- `nb_agent/core/context.py`

- `nb_agent/core/models.py`

- `nb_agent/core/retry.py`

- `nb_agent/core/__init__.py`

- `nb_agent/mcp/client.py`

- `nb_agent/mcp/__init__.py`

- `nb_agent/session/models.py`

- `nb_agent/session/store.py`

- `nb_agent/session/__init__.py`

- `nb_agent/skills/manager.py`

- `nb_agent/skills/__init__.py`

- `nb_agent/skills/builtin/code-review/SKILL.md`

- `nb_agent/skills/builtin/explain-code/SKILL.md`

- `nb_agent/skills/builtin/refactor/SKILL.md`

- `nb_agent/tools/base.py`

- `nb_agent/tools/builtin.py`

- `nb_agent/tools/__init__.py`

- `nb_agent/tui/app.py`

- `nb_agent/tui/styles.tcss`

- `nb_agent/tui/__init__.py`

- `nb_agent/tui/widgets/commands.py`

- `nb_agent/tui/widgets/inputs.py`

- `nb_agent/tui/widgets/screens.py`

- `nb_agent/tui/widgets/tool_panel.py`

- `nb_agent/tui/widgets/__init__.py`


---


--- **start of file: nb_agent/main.py** (project: nb_agent) --- 


### 📄 Python File Metadata: `nb_agent/main.py`

#### 📝 Module Docstring

`````
nb_agent CLI 入口
`````

#### 📦 Imports

- `import argparse`
- `import os`
- `import sys`
- `from nb_agent.config import load_config`
- `import asyncio`
- `from nb_agent.core import AgentCore`
- `from nb_agent.session import SessionStore`
- `from nb_agent.tui.app import AgentApp`

#### 🔧 Public Functions (1)

- `def main()`
  - *Line: 8*


---

`````python
"""nb_agent CLI 入口"""

import argparse
import os
import sys


def main():
    parser = argparse.ArgumentParser(description="nb_agent — Handwritten ReAct Agent with TUI")
    parser.add_argument("--config", "-c", help="配置文件路径 (JSONC)")
    parser.add_argument("--dotenv", help=".env 文件路径")

    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="非交互模式：执行一次对话")
    run_parser.add_argument("prompt", nargs="?", help="用户提问")
    run_parser.add_argument("-f", "--file", help="从文件读取 prompt")

    subparsers.add_parser("sessions", help="会话管理")

    args = parser.parse_args()

    from nb_agent.config import load_config
    config = load_config(
        cli_config_path=args.config or "",
        dotenv_path=args.dotenv or "",
    )
    config["_project_root"] = os.getcwd()

    if args.command == "run":
        _run_once(config, args)
    elif args.command == "sessions":
        _list_sessions(config)
    else:
        _run_tui(config)


def _run_tui(config: dict):
    try:
        from nb_agent.tui.app import AgentApp
    except ImportError:
        print("TUI 依赖未安装，请运行: pip install nb_agent[tui]")
        sys.exit(1)
    app = AgentApp(config)
    app.run()


def _run_once(config: dict, args):
    import asyncio

    prompt = args.prompt or ""
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            prompt = f.read()
    if not prompt:
        print("错误：请提供 prompt 或 -f 文件")
        sys.exit(1)

    from nb_agent.core import AgentCore

    async def _run():
        agent = AgentCore(config)
        await agent.connect_mcp()
        try:
            async for chunk in agent.chat_stream(prompt):
                print(chunk, end="", flush=True)
            print()
        finally:
            await agent.disconnect_mcp()

    asyncio.run(_run())


def _list_sessions(config: dict):
    from nb_agent.session import SessionStore
    db_path = config.get("session", {}).get("db_path", "")
    store = SessionStore(db_path)
    sessions = store.list_sessions(limit=20)
    if not sessions:
        print("暂无历史会话")
        return
    for s in sessions:
        print(f"  {s['id']}  {s['title'][:40]:<40}  {s['updated_at'][:19]}")


if __name__ == "__main__":
    main()

`````

--- **end of file: nb_agent/main.py** (project: nb_agent) --- 

---


--- **start of file: nb_agent/__init__.py** (project: nb_agent) --- 


### 📄 Python File Metadata: `nb_agent/__init__.py`

#### 📝 Module Docstring

`````
nb_agent — Handwritten ReAct Agent with TUI
`````


---

`````python
"""nb_agent — Handwritten ReAct Agent with TUI"""

__version__ = "0.1.0"

`````

--- **end of file: nb_agent/__init__.py** (project: nb_agent) --- 

---


--- **start of file: nb_agent/__main__.py** (project: nb_agent) --- 


### 📄 Python File Metadata: `nb_agent/__main__.py`

#### 📝 Module Docstring

`````
python -m nb_agent 入口
`````

#### 📦 Imports

- `from nb_agent.main import main`


---

`````python
"""python -m nb_agent 入口"""

from nb_agent.main import main

main()

`````

--- **end of file: nb_agent/__main__.py** (project: nb_agent) --- 

---


--- **start of file: nb_agent/approval/engine.py** (project: nb_agent) --- 


### 📄 Python File Metadata: `nb_agent/approval/engine.py`

#### 📝 Module Docstring

`````
工具审批规则引擎 — 判断工具调用是否需要用户确认
`````

#### 📦 Imports

- `from typing import Callable`
- `from typing import List`
- `from typing import Optional`

#### 🏛️ Classes (1)

##### 📌 `class ApprovalEngine`
*Line: 47*

**Docstring:**
`````
工具审批规则引擎：可插拔规则列表，任一命中即触发审批
`````

**🔧 Constructor (`__init__`):**
- `def __init__(self, rules: Optional[List[Callable]] = None, extra_dangerous: Optional[List[str]] = None)`
  - **Parameters:**
    - `self`
    - `rules: Optional[List[Callable]] = None`
    - `extra_dangerous: Optional[List[str]] = None`

**Public Methods (3):**
- `def needs_approval(self, tool_name: str, tool_kwargs: dict) -> bool`
- `def add_rule(self, rule: Callable)`
- `def remove_rule(self, rule: Callable)`

#### 🔧 Public Functions (2)

- `def rule_redis_write(tool_name: str, tool_kwargs: dict) -> bool`
  - *Line: 26*
  - *redis_execute 中的写命令需要审批*

- `def rule_dangerous_tools(tool_name: str, tool_kwargs: dict) -> bool`
  - *Line: 36*
  - *ALWAYS_APPROVE_TOOLS 名单中的工具始终需要审批*


---

`````python
"""工具审批规则引擎 — 判断工具调用是否需要用户确认"""

from typing import Callable, List, Optional


ALWAYS_APPROVE_TOOLS = {
    "mcp__dev-toolkit__kill_process",
    "mcp__redis-tools__redis_smart_set",
}

REDIS_WRITE_COMMANDS = {
    "SET", "SETNX", "SETEX", "PSETEX", "MSET", "MSETNX", "APPEND",
    "INCR", "INCRBY", "INCRBYFLOAT", "DECR", "DECRBY",
    "DEL", "UNLINK", "RENAME", "RENAMENX", "EXPIRE", "EXPIREAT",
    "PEXPIRE", "PEXPIREAT", "PERSIST", "MOVE", "COPY",
    "HSET", "HSETNX", "HMSET", "HDEL", "HINCRBY", "HINCRBYFLOAT",
    "LPUSH", "RPUSH", "LPOP", "RPOP", "LSET", "LINSERT", "LREM", "LTRIM",
    "SADD", "SREM", "SPOP", "SMOVE", "SDIFFSTORE", "SINTERSTORE", "SUNIONSTORE",
    "ZADD", "ZREM", "ZINCRBY", "ZPOPMIN", "ZPOPMAX",
    "XADD", "XDEL", "XTRIM",
    "PFADD", "PFMERGE",
    "GEOADD",
}


def rule_redis_write(tool_name: str, tool_kwargs: dict) -> bool:
    """redis_execute 中的写命令需要审批"""
    if tool_name != "mcp__redis-tools__redis_execute":
        return False
    cmd_parts = tool_kwargs.get("command", "").strip().split()
    if not cmd_parts:
        return False
    return cmd_parts[0].upper() in REDIS_WRITE_COMMANDS


def rule_dangerous_tools(tool_name: str, tool_kwargs: dict) -> bool:
    """ALWAYS_APPROVE_TOOLS 名单中的工具始终需要审批"""
    return tool_name in ALWAYS_APPROVE_TOOLS


DEFAULT_RULES: List[Callable[[str, dict], bool]] = [
    rule_redis_write,
    rule_dangerous_tools,
]


class ApprovalEngine:
    """工具审批规则引擎：可插拔规则列表，任一命中即触发审批"""

    def __init__(self, rules: Optional[List[Callable]] = None,
                 extra_dangerous: Optional[List[str]] = None):
        self.rules: List[Callable] = list(rules or DEFAULT_RULES)
        if extra_dangerous:
            extra_set = set(extra_dangerous)
            self.rules.append(lambda name, kwargs: name in extra_set)

    def needs_approval(self, tool_name: str, tool_kwargs: dict) -> bool:
        return any(rule(tool_name, tool_kwargs) for rule in self.rules)

    def add_rule(self, rule: Callable):
        self.rules.append(rule)

    def remove_rule(self, rule: Callable):
        self.rules = [r for r in self.rules if r is not rule]

`````

--- **end of file: nb_agent/approval/engine.py** (project: nb_agent) --- 

---


--- **start of file: nb_agent/approval/__init__.py** (project: nb_agent) --- 


### 📄 Python File Metadata: `nb_agent/approval/__init__.py`

#### 📦 Imports

- `from engine import ApprovalEngine`


---

`````python
from .engine import ApprovalEngine  # noqa: F401

`````

--- **end of file: nb_agent/approval/__init__.py** (project: nb_agent) --- 

---


--- **start of file: nb_agent/config/loader.py** (project: nb_agent) --- 


### 📄 Python File Metadata: `nb_agent/config/loader.py`

#### 📝 Module Docstring

`````
配置加载器 — JSONC 格式，支持环境变量替换

加载优先级: CLI 参数 > 环境变量 > 项目级 ./config.jsonc > 全局 ~/.nb_agent/config.jsonc > 默认值

支持 {env:VARIABLE_NAME} 语法从环境变量读取值。
缺失的环境变量替换为空字符串。
`````

#### 📦 Imports

- `import copy`
- `import os`
- `import re`
- `from pathlib import Path`
- `import json5`
- `from dotenv import load_dotenv`
- `import logging`
- `import logging`

#### 🔧 Public Functions (1)

- `def load_config(cli_config_path: str = '', dotenv_path: str = '') -> dict`
  - *Line: 75*
  - *加载配置，返回合并后的配置字典*


---

`````python
"""
配置加载器 — JSONC 格式，支持环境变量替换

加载优先级: CLI 参数 > 环境变量 > 项目级 ./config.jsonc > 全局 ~/.nb_agent/config.jsonc > 默认值

支持 {env:VARIABLE_NAME} 语法从环境变量读取值。
缺失的环境变量替换为空字符串。
"""

import copy
import os
import re
from pathlib import Path

import json5
from dotenv import load_dotenv


DEFAULT_CONFIG = {
    "agent": {
        "system_prompt": "你是一个智能助手。",
        "default_model": "",
        "max_context_tokens": 0,
        "streaming": True,
    },
    "provider": {},
    "mcp": {},
    "approval": {
        "dangerous_tools": [],
        "auto_approve": False,
    },
    "session": {
        "db_path": "",
    },
    "ui": {
        "theme": "dark",
        "show_tool_panel": True,
        "show_token_usage": True,
    },
}


def _substitute_env(text: str) -> str:
    """将 {env:VAR_NAME} 替换为对应环境变量值，缺失则替换为空字符串"""
    return re.sub(r"\{env:([^}]+)\}", lambda m: os.environ.get(m.group(1), ""), text)


def _find_config_file(cli_path: str = "") -> str:
    """按优先级查找配置文件"""
    if cli_path:
        return cli_path

    cwd_config = os.path.join(os.getcwd(), "config.jsonc")
    if os.path.isfile(cwd_config):
        return cwd_config

    home_config = os.path.join(Path.home(), ".nb_agent", "config.jsonc")
    if os.path.isfile(home_config):
        return home_config

    return ""


def _deep_merge(base: dict, override: dict) -> dict:
    """深度合并字典，override 覆盖 base"""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(cli_config_path: str = "", dotenv_path: str = "") -> dict:
    """加载配置，返回合并后的配置字典"""
    if dotenv_path:
        load_dotenv(dotenv_path, override=False)
    else:
        load_dotenv(override=False)

    config_path = _find_config_file(cli_config_path)
    if not config_path:
        return copy.deepcopy(DEFAULT_CONFIG)

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            raw = f.read()
    except (FileNotFoundError, PermissionError) as e:
        import logging
        logging.warning(f"配置文件读取失败: {e}，使用默认配置")
        return copy.deepcopy(DEFAULT_CONFIG)

    raw = _substitute_env(raw)
    try:
        user_config = json5.loads(raw)
    except ValueError as e:
        import logging
        logging.warning(f"配置文件解析失败: {e}，使用默认配置")
        return copy.deepcopy(DEFAULT_CONFIG)

    merged = _deep_merge(copy.deepcopy(DEFAULT_CONFIG), user_config)
    merged["_config_path"] = config_path
    merged["_project_root"] = os.path.dirname(os.path.abspath(config_path))

    return merged

`````

--- **end of file: nb_agent/config/loader.py** (project: nb_agent) --- 

---


--- **start of file: nb_agent/config/__init__.py** (project: nb_agent) --- 


### 📄 Python File Metadata: `nb_agent/config/__init__.py`

#### 📦 Imports

- `from loader import load_config`


---

`````python
from .loader import load_config  # noqa: F401

`````

--- **end of file: nb_agent/config/__init__.py** (project: nb_agent) --- 

---


--- **start of file: nb_agent/core/agent.py** (project: nb_agent) --- 


### 📄 Python File Metadata: `nb_agent/core/agent.py`

#### 📝 Module Docstring

`````
AgentCore — ReAct 循环核心

核心循环：
  用户输入 → LLM(messages + tools) → 判断:
    有 tool_calls → 执行工具 → 结果回传 LLM → 再次判断（可能多轮）
    无 tool_calls → 返回文本回复
`````

#### 📦 Imports

- `import asyncio`
- `import functools`
- `import json`
- `import uuid`
- `from typing import AsyncIterator`
- `from typing import List`
- `from typing import Dict`
- `from typing import Optional`
- `from typing import Callable`
- `from openai import AsyncOpenAI`
- `from nb_agent.core.models import ModelInfo`
- `from nb_agent.core.models import ToolCallRecord`
- `from nb_agent.core.models import AgentResponse`
- `from nb_agent.core.models import load_models_from_config`
- `from nb_agent.core.context import trim_context`
- `from nb_agent.core.retry import call_llm_with_retry`
- `from nb_agent.core.retry import RETRYABLE_ERRORS`
- `from nb_agent.core.retry import MAX_RETRIES`
- `from nb_agent.session import SessionStore`
- `from nb_agent.mcp import MCPManager`
- `from nb_agent.approval import ApprovalEngine`
- `from nb_agent.tools import TOOL_REGISTRY`
- `from nb_agent.skills import SkillManager`

#### 🏛️ Classes (1)

##### 📌 `class AgentCore`
*Line: 30*

**Docstring:**
`````
Agent 核心：
- Function Calling：LLM 自主决定是否调用工具
- 多轮工具调用：一次对话中可调用多个工具、多轮
- 通过回调实时通知 TUI 工具调用状态
`````

**🔧 Constructor (`__init__`):**
- `def __init__(self, config: dict)`
  - **Parameters:**
    - `self`
    - `config: dict`

**Public Methods (18):**
- `async def chat(self, user_input: str) -> AgentResponse`
- `async def chat_stream(self, user_input: str) -> AsyncIterator[str]`
  - *工具调用阶段用非流式（需要完整 tool_calls），最终回复用流式输出*
- `async def connect_mcp(self)`
- `async def disconnect_mcp(self)`
- `def switch_model(self, model_id: str) -> bool`
- `def get_models_grouped(self) -> Dict[str, List[ModelInfo]]`
- `async def generate_smart_title(self)`
- `def clear_history(self)`
- `def get_session_list(self, limit: int = 50) -> list`
- `def get_tools(self) -> list`
- `def get_tool_groups(self) -> list`
  - *返回所有工具分组及其状态*
- `def toggle_tool_group(self, group: str) -> bool`
  - *切换工具分组的启用/禁用状态，返回 True=已启用*
- `def get_mcp_status(self) -> list`
- `def toggle_mcp_server(self, name: str) -> bool`
- `def get_model_name(self) -> str`
- `def get_model_display_name(self) -> str`
- `def get_token_usage(self) -> dict`
- `def register_tool(self, name: str, func: Callable, description: str, parameters: dict, group: str = '')`

**Class Variables (1):**
- `MAX_TOOL_ROUNDS = 30`


---

`````python
"""
AgentCore — ReAct 循环核心

核心循环：
  用户输入 → LLM(messages + tools) → 判断:
    有 tool_calls → 执行工具 → 结果回传 LLM → 再次判断（可能多轮）
    无 tool_calls → 返回文本回复
"""

import asyncio
import functools
import json
import uuid
from typing import AsyncIterator, List, Dict, Optional, Callable

from openai import AsyncOpenAI

from nb_agent.core.models import (
    ModelInfo, ToolCallRecord, AgentResponse, load_models_from_config,
)
from nb_agent.core.context import trim_context
from nb_agent.core.retry import call_llm_with_retry, RETRYABLE_ERRORS, MAX_RETRIES
from nb_agent.session import SessionStore
from nb_agent.mcp import MCPManager
from nb_agent.approval import ApprovalEngine
from nb_agent.tools import TOOL_REGISTRY
from nb_agent.skills import SkillManager


class AgentCore:
    """
    Agent 核心：
    - Function Calling：LLM 自主决定是否调用工具
    - 多轮工具调用：一次对话中可调用多个工具、多轮
    - 通过回调实时通知 TUI 工具调用状态
    """

    MAX_TOOL_ROUNDS = 30

    def __init__(self, config: dict):
        self.config = config
        base_prompt = config.get("agent", {}).get("system_prompt", "你是一个智能助手。")
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.last_turn_prompt = 0
        self.last_turn_completion = 0
        self.last_turn_tool_calls = 0

        self.tool_registry: Dict[str, dict] = dict(TOOL_REGISTRY)

        project_root = config.get("_project_root", "")
        self.skill_manager = SkillManager(
            project_root=__import__("pathlib").Path(project_root) if project_root else None
        )
        self.skill_manager.discover()
        self.system_prompt = self._build_system_prompt(base_prompt)
        self.messages: List[dict] = [{"role": "system", "content": self.system_prompt}]

        self.available_models: List[ModelInfo] = load_models_from_config(config)
        self.current_model: Optional[ModelInfo] = None
        self._llm_clients: Dict[str, AsyncOpenAI] = {}
        self._select_default_model()

        self.on_tool_call: Optional[Callable] = None
        self.approval_callback: Optional[Callable] = None

        extra_dangerous = config.get("approval", {}).get("dangerous_tools", [])
        self.approval_engine = ApprovalEngine(extra_dangerous=extra_dangerous or None)

        self.disabled_tool_groups: set = set()

        self.mcp_manager = MCPManager()

        db_path = config.get("session", {}).get("db_path", "")
        self.session_store = SessionStore(db_path)
        self.session_id = str(uuid.uuid4())[:8]
        model_id = self.current_model.id if self.current_model else ""
        self.session_store.create_session(self.session_id, title="新会话", model_id=model_id)

    def _build_system_prompt(self, base_prompt: str) -> str:
        """在用户 system_prompt 末尾追加 Skills 清单（渐进式披露）"""
        manifest = self.skill_manager.get_manifest()
        if not manifest:
            return base_prompt
        lines = [
            base_prompt,
            "",
            "## 可用 Skills",
            "以下是你可以使用的技能指南。当任务匹配某个 Skill 时，先调用 `view_skill` 工具获取完整指南再执行。",
            "",
        ]
        for s in manifest:
            lines.append(f"- **{s['name']}**: {s['description']}")
        lines.append("")
        lines.append("调用方式: `view_skill(skill_name=\"<name>\")` 获取完整指南内容。")
        return "\n".join(lines)

    def _select_default_model(self):
        default = self.config.get("agent", {}).get("default_model", "")
        if default:
            for m in self.available_models:
                if m.id == default:
                    self.current_model = m
                    break
        if not self.current_model and self.available_models:
            self.current_model = self.available_models[0]

    def _get_client(self, model: ModelInfo) -> AsyncOpenAI:
        key = model.provider
        if key not in self._llm_clients:
            self._llm_clients[key] = AsyncOpenAI(
                base_url=model.base_url,
                api_key=model.api_key,
            )
        return self._llm_clients[key]

    def _get_openai_tools(self) -> list:
        """合并内置 tools + MCP tools + Skills view_skill，过滤 disabled groups"""
        tools = []
        for t in self.tool_registry.values():
            group = t.get("group", "")
            if group and group in self.disabled_tool_groups:
                continue
            tools.append(t["schema"])
        tools.extend(self.mcp_manager.get_all_tools_openai_format())
        if self.skill_manager.get_manifest():
            tools.append(self.skill_manager.get_view_skill_schema())
        return tools

    async def _execute_with_approval(self, name: str, args: dict) -> str:
        if self.approval_engine.needs_approval(name, args):
            if not self.approval_callback:
                return "[已拦截] 此操作需要审批但无审批通道，已自动拒绝"
            approved = await self.approval_callback(name, args)
            if not approved:
                return "[用户已拒绝执行此操作]"
        return await self._execute_tool(name, args)

    async def _execute_tool(self, name: str, args: dict) -> str:
        if name == "view_skill":
            skill_name = args.get("skill_name", "")
            result = self.skill_manager.view_skill(skill_name)
            if result["success"]:
                return result["content"]
            return json.dumps(result, ensure_ascii=False)

        if self.mcp_manager.is_mcp_tool(name):
            return await self.mcp_manager.call_tool(name, args)
        tool_info = self.tool_registry.get(name)
        if not tool_info:
            return f"错误: 未知工具 '{name}'"

        func = tool_info["function"]
        model_cls = tool_info.get("model_cls")
        try:
            if model_cls:
                params = model_cls(**args)
                if asyncio.iscoroutinefunction(func):
                    result = await func(params)
                else:
                    result = await asyncio.get_running_loop().run_in_executor(
                        None, functools.partial(func, params)
                    )
            else:
                if asyncio.iscoroutinefunction(func):
                    result = await func(**args)
                else:
                    result = await asyncio.get_running_loop().run_in_executor(
                        None, functools.partial(func, **args)
                    )
            return str(result)
        except Exception as e:
            return f"工具执行失败: {type(e).__name__}: {e}"

    def _clean_messages_for_api(self) -> list:
        return [
            {k: v for k, v in m.items() if not k.startswith('_')}
            for m in self.messages
        ]

    def _build_assistant_msg(self, resp_msg) -> dict:
        msg = {"role": "assistant", "content": resp_msg.content or ""}
        msg["_model"] = self.current_model.id if self.current_model else ""

        if resp_msg.tool_calls:
            msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in resp_msg.tool_calls
            ]
            if not msg["content"]:
                msg["content"] = None

        reasoning = getattr(resp_msg, "reasoning_content", None)
        if reasoning:
            msg["reasoning_content"] = reasoning

        return msg

    # ==================== 非流式 ====================

    async def chat(self, user_input: str) -> AgentResponse:
        self.messages.append({"role": "user", "content": user_input})
        self.messages = trim_context(
            self.messages,
            self.current_model.context_limit if self.current_model else 0,
        )
        self.session_store.save_message(self.session_id, "user", user_input)
        self._auto_update_title(user_input)

        if not self.current_model:
            return AgentResponse(text="[错误] 没有配置任何模型")

        client = self._get_client(self.current_model)
        openai_tools = self._get_openai_tools()
        all_tool_calls: list = []
        self.last_turn_prompt = 0
        self.last_turn_completion = 0
        self.last_turn_tool_calls = 0

        for round_idx in range(self.MAX_TOOL_ROUNDS):
            try:
                kwargs = {
                    "model": self.current_model.id,
                    "messages": self._clean_messages_for_api(),
                }
                if openai_tools:
                    kwargs["tools"] = openai_tools

                resp = await call_llm_with_retry(client, **kwargs)
                resp_msg = resp.choices[0].message

                if resp.usage:
                    p = resp.usage.prompt_tokens or 0
                    c = resp.usage.completion_tokens or 0
                    self.last_turn_prompt += p
                    self.last_turn_completion += c
                    self.total_prompt_tokens += p
                    self.total_completion_tokens += c

                if not resp_msg.tool_calls:
                    reply = resp_msg.content or ""
                    reasoning = getattr(resp_msg, "reasoning_content", "") or ""
                    self.messages.append(self._build_assistant_msg(resp_msg))
                    tc_dicts = [{"name": t.name, "args": t.args, "result": t.result} for t in all_tool_calls]
                    self.session_store.save_message(
                        self.session_id, "assistant", reply,
                        reasoning=reasoning, tool_calls=tc_dicts,
                    )
                    return AgentResponse(
                        text=reply, reasoning=reasoning,
                        tool_calls=all_tool_calls, token_usage=self.get_token_usage(),
                    )

                self.messages.append(self._build_assistant_msg(resp_msg))

                for tc in resp_msg.tool_calls:
                    func_name = tc.function.name
                    try:
                        func_args = json.loads(tc.function.arguments)
                    except json.JSONDecodeError:
                        func_args = {}

                    record = ToolCallRecord(name=func_name, args=func_args, status="running")
                    all_tool_calls.append(record)
                    self.last_turn_tool_calls += 1

                    if self.on_tool_call:
                        self.on_tool_call(record)

                    result = await self._execute_with_approval(func_name, func_args)
                    record.result = result
                    record.status = "error" if result.startswith(("[已拦截]", "[用户已拒绝", "错误:", "工具执行失败")) else "done"

                    if self.on_tool_call:
                        self.on_tool_call(record)

                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    })

            except RETRYABLE_ERRORS as e:
                error_text = f"[网络/超时错误（已重试 {MAX_RETRIES} 次）] {type(e).__name__}: {e}"
                self.messages.append({"role": "assistant", "content": error_text})
                return AgentResponse(text=error_text, tool_calls=all_tool_calls, token_usage=self.get_token_usage())
            except Exception as e:
                error_text = f"[LLM 调用失败] {type(e).__name__}: {e}"
                self.messages.append({"role": "assistant", "content": error_text})
                return AgentResponse(text=error_text, tool_calls=all_tool_calls, token_usage=self.get_token_usage())

        return AgentResponse(
            text="[警告] 工具调用轮次超限，已强制停止",
            tool_calls=all_tool_calls, token_usage=self.get_token_usage(),
        )

    # ==================== 流式 ====================

    async def chat_stream(self, user_input: str) -> AsyncIterator[str]:
        """工具调用阶段用非流式（需要完整 tool_calls），最终回复用流式输出"""
        self.messages.append({"role": "user", "content": user_input})
        self.messages = trim_context(
            self.messages,
            self.current_model.context_limit if self.current_model else 0,
        )
        self.session_store.save_message(self.session_id, "user", user_input)
        self._auto_update_title(user_input)

        if not self.current_model:
            yield "[错误] 没有配置任何模型"
            return

        client = self._get_client(self.current_model)
        openai_tools = self._get_openai_tools()
        self.last_turn_prompt = 0
        self.last_turn_completion = 0
        self.last_turn_tool_calls = 0

        for round_idx in range(self.MAX_TOOL_ROUNDS):
            try:
                kwargs = {
                    "model": self.current_model.id,
                    "messages": self._clean_messages_for_api(),
                    "stream": True,
                }
                if self.current_model.base_url and "openai.com" in self.current_model.base_url:
                    kwargs["stream_options"] = {"include_usage": True}
                elif self.current_model.base_url and "deepseek.com" in self.current_model.base_url:
                    kwargs["stream_options"] = {"include_usage": True}
                if openai_tools:
                    kwargs["tools"] = openai_tools

                stream_resp = await call_llm_with_retry(client, **kwargs)

                full_content = ""
                full_reasoning = ""
                tool_calls_map: Dict[int, dict] = {}
                in_thinking = False
                has_tool_calls = False
                chunk = None

                async for chunk in stream_resp:
                    delta = chunk.choices[0].delta if chunk.choices else None
                    if not delta:
                        continue

                    reasoning_chunk = getattr(delta, "reasoning_content", None) or ""
                    if reasoning_chunk:
                        if not in_thinking:
                            in_thinking = True
                            yield "<think>"
                        full_reasoning += reasoning_chunk
                        yield reasoning_chunk

                    content_chunk = delta.content or ""
                    if content_chunk:
                        if in_thinking:
                            in_thinking = False
                            yield "</think>"
                        full_content += content_chunk
                        yield content_chunk

                    if delta.tool_calls:
                        has_tool_calls = True
                        for tc_delta in delta.tool_calls:
                            idx = tc_delta.index
                            if idx not in tool_calls_map:
                                tool_calls_map[idx] = {"id": tc_delta.id or "", "name": "", "arguments": ""}
                            if tc_delta.function:
                                if tc_delta.function.name:
                                    tool_calls_map[idx]["name"] = tc_delta.function.name
                                if tc_delta.function.arguments:
                                    tool_calls_map[idx]["arguments"] += tc_delta.function.arguments

                if in_thinking:
                    yield "</think>"

                if chunk and hasattr(chunk, 'usage') and chunk.usage:
                    p = chunk.usage.prompt_tokens or 0
                    c = chunk.usage.completion_tokens or 0
                    self.last_turn_prompt += p
                    self.last_turn_completion += c
                    self.total_prompt_tokens += p
                    self.total_completion_tokens += c

                if not has_tool_calls:
                    msg = {"role": "assistant", "content": full_content}
                    msg["_model"] = self.current_model.id if self.current_model else ""
                    if full_reasoning:
                        msg["reasoning_content"] = full_reasoning
                    self.messages.append(msg)
                    self.session_store.save_message(
                        self.session_id, "assistant", full_content, reasoning=full_reasoning,
                    )
                    return

                assembled_tool_calls = []
                for idx in sorted(tool_calls_map.keys()):
                    tc = tool_calls_map[idx]
                    assembled_tool_calls.append({
                        "id": tc["id"],
                        "type": "function",
                        "function": {"name": tc["name"], "arguments": tc["arguments"]},
                    })

                msg = {
                    "role": "assistant",
                    "content": full_content or None,
                    "tool_calls": assembled_tool_calls,
                    "_model": self.current_model.id if self.current_model else "",
                }
                if full_reasoning:
                    msg["reasoning_content"] = full_reasoning
                self.messages.append(msg)

                stream_tool_records = []
                for tc in assembled_tool_calls:
                    func_name = tc["function"]["name"]
                    try:
                        func_args = json.loads(tc["function"]["arguments"])
                    except json.JSONDecodeError:
                        func_args = {}

                    self.last_turn_tool_calls += 1
                    yield f"\n🔧 调用工具: {func_name}({json.dumps(func_args, ensure_ascii=False)})\n"

                    result = await self._execute_with_approval(func_name, func_args)
                    stream_tool_records.append({"name": func_name, "args": func_args, "result": result})

                    yield f"📋 结果: {result}\n"

                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": result,
                    })

                self.session_store.save_message(
                    self.session_id, "assistant", full_content,
                    reasoning=full_reasoning, tool_calls=stream_tool_records,
                )

            except RETRYABLE_ERRORS as e:
                yield f"\n[网络/超时错误（已重试 {MAX_RETRIES} 次）] {type(e).__name__}: {e}"
                return
            except Exception as e:
                yield f"\n[LLM 调用失败] {type(e).__name__}: {e}"
                return

        yield "\n[警告] 工具调用轮次超限"

    # ==================== MCP ====================

    async def connect_mcp(self):
        mcp_config = self.config.get("mcp", {})
        project_root = self.config.get("_project_root", "")
        if mcp_config:
            await self.mcp_manager.connect_all(mcp_config, project_root=project_root)

    async def disconnect_mcp(self):
        await self.mcp_manager.disconnect_all()

    # ==================== 查询接口 ====================

    def switch_model(self, model_id: str) -> bool:
        for m in self.available_models:
            if m.id == model_id:
                self.current_model = m
                return True
        return False

    def get_models_grouped(self) -> Dict[str, List[ModelInfo]]:
        groups: Dict[str, List[ModelInfo]] = {}
        for m in self.available_models:
            groups.setdefault(m.provider_name, []).append(m)
        return groups

    def _auto_update_title(self, user_input: str):
        current_title = self.session_store.get_session_title(self.session_id)
        if current_title == "新会话":
            title = user_input[:30].replace("\n", " ").strip()
            if title:
                self.session_store.update_session_title(self.session_id, title)

    async def generate_smart_title(self):
        current_title = self.session_store.get_session_title(self.session_id)
        if not current_title or current_title == "新会话":
            return
        user_msgs = [m["content"] for m in self.messages if m.get("role") == "user"]
        if not user_msgs:
            return
        first_msg = user_msgs[0][:200]
        try:
            if not self.current_model:
                return
            client = self._get_client(self.current_model)
            resp = await client.chat.completions.create(
                model=self.current_model.id,
                messages=[
                    {"role": "system", "content": "你是一个标题生成器。根据用户的问题，生成一个不超过10个字的简短标题。只输出标题文字，不加引号或标点。"},
                    {"role": "user", "content": first_msg},
                ],
                max_tokens=20,
                temperature=0.3,
            )
            title = (resp.choices[0].message.content or "").strip().strip('"\'')
            if title and len(title) <= 30:
                self.session_store.update_session_title(self.session_id, title)
        except Exception:
            pass

    def clear_history(self):
        self.messages = [{"role": "system", "content": self.system_prompt}]
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.last_turn_prompt = 0
        self.last_turn_completion = 0
        self.last_turn_tool_calls = 0
        self.session_id = str(uuid.uuid4())[:8]
        model_id = self.current_model.id if self.current_model else ""
        self.session_store.create_session(self.session_id, title="新会话", model_id=model_id)

    def get_session_list(self, limit: int = 50) -> list:
        return self.session_store.list_sessions(limit)

    def get_tools(self) -> list:
        builtin = []
        for name, t in self.tool_registry.items():
            group = t.get("group", "")
            builtin.append({
                "name": name,
                "func_name": t.get("func_name", name),
                "group": group,
                "description": t["schema"]["function"]["description"],
                "source": "内置",
                "disabled": group in self.disabled_tool_groups if group else False,
            })
        if self.skill_manager.get_manifest():
            builtin.append({
                "name": "view_skill",
                "func_name": "view_skill",
                "group": "",
                "description": "查看 Skill 完整指南",
                "source": "Skills",
                "disabled": False,
            })
        mcp_tools = []
        for t in self.mcp_manager.get_tool_info_list():
            server = t["server"]
            mcp_tools.append({
                "name": f"mcp__{server}__{t['name']}",
                "func_name": t["name"],
                "group": f"mcp__{server}",
                "description": t["description"],
                "source": f"MCP:{server}",
                "disabled": self.mcp_manager.is_server_disabled(server),
            })
        return builtin + mcp_tools

    def get_tool_groups(self) -> list:
        """返回所有工具分组及其状态"""
        groups = {}
        for t in self.get_tools():
            group = t.get("group", "")
            if not group:
                group = "(无分组)"
            if group not in groups:
                groups[group] = {"name": group, "count": 0, "disabled": False, "source": t["source"]}
            groups[group]["count"] += 1
            groups[group]["disabled"] = t.get("disabled", False)
        return sorted(groups.values(), key=lambda g: g["name"])

    def toggle_tool_group(self, group: str) -> bool:
        """切换工具分组的启用/禁用状态，返回 True=已启用"""
        if group.startswith("mcp__"):
            server_name = group[5:]
            return self.mcp_manager.toggle_server(server_name)
        if group in self.disabled_tool_groups:
            self.disabled_tool_groups.discard(group)
            return True
        self.disabled_tool_groups.add(group)
        return False

    def get_mcp_status(self) -> list:
        return self.mcp_manager.get_server_status()

    def toggle_mcp_server(self, name: str) -> bool:
        return self.mcp_manager.toggle_server(name)

    def get_model_name(self) -> str:
        return self.current_model.id if self.current_model else "未配置"

    def get_model_display_name(self) -> str:
        return self.current_model.name if self.current_model else "未配置"

    def get_token_usage(self) -> dict:
        return {
            "last_prompt": self.last_turn_prompt,
            "last_completion": self.last_turn_completion,
            "last_total": self.last_turn_prompt + self.last_turn_completion,
            "last_tool_calls": self.last_turn_tool_calls,
            "total_prompt": self.total_prompt_tokens,
            "total_completion": self.total_completion_tokens,
            "total": self.total_prompt_tokens + self.total_completion_tokens,
        }

    def register_tool(self, name: str, func: Callable, description: str,
                      parameters: dict, group: str = ""):
        tool_name = f"{group}__{name}" if group else name
        self.tool_registry[tool_name] = {
            "function": func,
            "group": group,
            "func_name": name,
            "schema": {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": description,
                    "parameters": parameters,
                },
            },
        }

`````

--- **end of file: nb_agent/core/agent.py** (project: nb_agent) --- 

---


--- **start of file: nb_agent/core/context.py** (project: nb_agent) --- 


### 📄 Python File Metadata: `nb_agent/core/context.py`

#### 📝 Module Docstring

`````
上下文窗口管理 — token 估算 + 自动裁剪
`````

#### 📦 Imports

- `from typing import List`

#### 🔧 Public Functions (2)

- `def estimate_tokens(text: str) -> int`
  - *Line: 6*
  - *粗略估算 token 数（中文约 1.5 字/token，英文约 4 字符/token）*

- `def trim_context(messages: List[dict], context_limit: int) -> List[dict]`
  - *Line: 26*
  - **Docstring:**
  `````
  当消息总 token 超出模型限制时，从最早的非 system 消息开始移除
  
  注意：此函数会原地修改传入的 messages 列表。
  `````


---

`````python
"""上下文窗口管理 — token 估算 + 自动裁剪"""

from typing import List


def estimate_tokens(text: str) -> int:
    """粗略估算 token 数（中文约 1.5 字/token，英文约 4 字符/token）"""
    if not text:
        return 0
    cn_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    en_chars = len(text) - cn_chars
    return int(cn_chars / 1.5 + en_chars / 4)


def _estimate_message_tokens(msg: dict) -> int:
    """估算单条消息的总 token（包括 content、reasoning、tool_calls）"""
    total = estimate_tokens(msg.get("content", "") or "")
    total += estimate_tokens(msg.get("reasoning_content", "") or "")
    for tc in msg.get("tool_calls", []):
        func = tc.get("function", {})
        total += estimate_tokens(func.get("name", ""))
        total += estimate_tokens(func.get("arguments", ""))
    return total


def trim_context(messages: List[dict], context_limit: int) -> List[dict]:
    """当消息总 token 超出模型限制时，从最早的非 system 消息开始移除

    注意：此函数会原地修改传入的 messages 列表。
    """
    if not context_limit:
        return messages

    max_tokens = int(context_limit * 0.85)

    total = sum(_estimate_message_tokens(m) for m in messages)

    while total > max_tokens and len(messages) > 2:
        removed = messages.pop(1)
        total -= _estimate_message_tokens(removed)

    return messages

`````

--- **end of file: nb_agent/core/context.py** (project: nb_agent) --- 

---


--- **start of file: nb_agent/core/models.py** (project: nb_agent) --- 


### 📄 Python File Metadata: `nb_agent/core/models.py`

#### 📝 Module Docstring

`````
数据结构 — AgentCore 使用的 dataclass
`````

#### 📦 Imports

- `from dataclasses import dataclass`
- `from dataclasses import field`
- `from typing import List`

#### 🏛️ Classes (3)

##### 📌 `class ToolCallRecord`
*Line: 8*

**Docstring:**
`````
工具调用记录（给 TUI 展示用）
`````

**Class Variables (4):**
- `name: str`
- `args: dict`
- `result: str = ''`
- `status: str = 'pending'`

##### 📌 `class AgentResponse`
*Line: 17*

**Docstring:**
`````
Agent 的回复
`````

**Class Variables (4):**
- `text: str`
- `reasoning: str = ''`
- `tool_calls: list = field(default_factory=list)`
- `token_usage: dict = field(default_factory=dict)`

##### 📌 `class ModelInfo`
*Line: 26*

**Docstring:**
`````
模型信息
`````

**Class Variables (8):**
- `id: str`
- `name: str`
- `provider: str`
- `provider_name: str`
- `base_url: str`
- `api_key: str`
- `context_limit: int = 0`
- `output_limit: int = 0`

#### 🔧 Public Functions (1)

- `def load_models_from_config(config: dict) -> List[ModelInfo]`
  - *Line: 38*
  - *从 config.jsonc 的 provider 节解析所有模型*


---

`````python
"""数据结构 — AgentCore 使用的 dataclass"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class ToolCallRecord:
    """工具调用记录（给 TUI 展示用）"""
    name: str
    args: dict
    result: str = ""
    status: str = "pending"  # pending / running / done / error


@dataclass
class AgentResponse:
    """Agent 的回复"""
    text: str
    reasoning: str = ""
    tool_calls: list = field(default_factory=list)
    token_usage: dict = field(default_factory=dict)


@dataclass
class ModelInfo:
    """模型信息"""
    id: str
    name: str
    provider: str
    provider_name: str
    base_url: str
    api_key: str
    context_limit: int = 0
    output_limit: int = 0


def load_models_from_config(config: dict) -> List[ModelInfo]:
    """从 config.jsonc 的 provider 节解析所有模型"""
    models = []
    for provider_id, provider_cfg in config.get("provider", {}).items():
        provider_name = provider_cfg.get("name", provider_id)
        base_url = provider_cfg.get("base_url", "")
        api_key = provider_cfg.get("api_key", "")

        for model_id, model_cfg in provider_cfg.get("models", {}).items():
            limit = model_cfg.get("limit", {})
            models.append(ModelInfo(
                id=model_id,
                name=model_cfg.get("name", model_id),
                provider=provider_id,
                provider_name=provider_name,
                base_url=base_url,
                api_key=api_key,
                context_limit=limit.get("context", 0),
                output_limit=limit.get("output", 0),
            ))
    return models

`````

--- **end of file: nb_agent/core/models.py** (project: nb_agent) --- 

---


--- **start of file: nb_agent/core/retry.py** (project: nb_agent) --- 


### 📄 Python File Metadata: `nb_agent/core/retry.py`

#### 📝 Module Docstring

`````
LLM 调用重试 — 指数退避
`````

#### 📦 Imports

- `import asyncio`
- `from openai import APITimeoutError`
- `from openai import RateLimitError`
- `from openai import APIConnectionError`

#### 🔧 Public Functions (1)

- `async def call_llm_with_retry(client, **kwargs)`
  - *Line: 12*
  - *带重试的 LLM 调用（超时/限流/网络错误自动重试）*


---

`````python
"""LLM 调用重试 — 指数退避"""

import asyncio
from openai import APITimeoutError, RateLimitError, APIConnectionError


MAX_RETRIES = 3
RETRY_DELAYS = [1, 3, 5]
RETRYABLE_ERRORS = (APITimeoutError, RateLimitError, APIConnectionError, ConnectionError, TimeoutError)


async def call_llm_with_retry(client, **kwargs):
    """带重试的 LLM 调用（超时/限流/网络错误自动重试）"""
    last_error: Exception = RuntimeError("LLM 调用失败（未知错误）")
    for attempt in range(MAX_RETRIES):
        try:
            return await client.chat.completions.create(**kwargs)
        except RETRYABLE_ERRORS as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
                await asyncio.sleep(delay)
    raise last_error

`````

--- **end of file: nb_agent/core/retry.py** (project: nb_agent) --- 

---


--- **start of file: nb_agent/core/__init__.py** (project: nb_agent) --- 


### 📄 Python File Metadata: `nb_agent/core/__init__.py`

#### 📦 Imports

- `from agent import AgentCore`
- `from models import ModelInfo`
- `from models import ToolCallRecord`
- `from models import AgentResponse`


---

`````python
from .agent import AgentCore  # noqa: F401
from .models import ModelInfo, ToolCallRecord, AgentResponse  # noqa: F401

`````

--- **end of file: nb_agent/core/__init__.py** (project: nb_agent) --- 

---


--- **start of file: nb_agent/mcp/client.py** (project: nb_agent) --- 


### 📄 Python File Metadata: `nb_agent/mcp/client.py`

#### 📝 Module Docstring

`````
MCP 客户端管理器 — 连接多个 MCP Server，统一管理工具

支持三种传输方式:
  - local (stdio): 启动子进程，通过 stdin/stdout 通信
  - sse: 通过 SSE 连接远程 MCP Server
  - streamableHttp: 通过 Streamable HTTP 连接远程 MCP Server
`````

#### 📦 Imports

- `import asyncio`
- `import contextlib`
- `import json`
- `import logging`
- `import os`
- `from typing import Dict`
- `from typing import List`
- `from typing import Optional`
- `from typing import Any`
- `from mcp import ClientSession`
- `from mcp.client.stdio import stdio_client`
- `from mcp.client.stdio import StdioServerParameters`
- `from mcp.client.sse import sse_client`
- `from mcp.client.streamable_http import streamablehttp_client`

#### 🏛️ Classes (2)

##### 📌 `class MCPServerInfo`
*Line: 40*

**Docstring:**
`````
单个 MCP Server 的连接信息
`````

**🔧 Constructor (`__init__`):**
- `def __init__(self, name: str, session = None)`
  - **Parameters:**
    - `self`
    - `name: str`
    - `session = None`

##### 📌 `class MCPManager`
*Line: 52*

**Docstring:**
`````
管理多个 MCP Server 的连接和工具调用
`````

**🔧 Constructor (`__init__`):**
- `def __init__(self)`
  - **Parameters:**
    - `self`

**Public Methods (10):**
- `async def connect_all(self, mcp_config: dict, project_root: str = '')`
  - **Docstring:**
  `````
  根据配置连接所有 MCP Server
  
  SSE/HTTP 连接必须在调用者任务中初始化（anyio cancel scope 要求），
  因此只有 stdio 类型才能用 asyncio.gather 并发启动。
  `````
- `async def connect_server(self, name: str, cfg: dict)`
  - *连接单个 MCP Server*
- `async def disconnect_all(self)`
- `def toggle_server(self, name: str) -> bool`
- `def is_server_disabled(self, name: str) -> bool`
- `def get_all_tools_openai_format(self) -> List[dict]`
- `def get_tool_info_list(self) -> List[dict]`
- `def get_server_status(self) -> List[dict]`
- `async def call_tool(self, full_tool_name: str, arguments: dict) -> str`
  - *调用 MCP 工具。full_tool_name 格式: mcp__{server}__{tool}*
- `def is_mcp_tool(self, tool_name: str) -> bool`


---

`````python
"""
MCP 客户端管理器 — 连接多个 MCP Server，统一管理工具

支持三种传输方式:
  - local (stdio): 启动子进程，通过 stdin/stdout 通信
  - sse: 通过 SSE 连接远程 MCP Server
  - streamableHttp: 通过 Streamable HTTP 连接远程 MCP Server
"""

import asyncio
import contextlib
import json
import logging
import os
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

try:
    from mcp import ClientSession
    from mcp.client.stdio import stdio_client, StdioServerParameters
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logger.warning("MCP SDK 未安装，请运行: pip install mcp")

try:
    from mcp.client.sse import sse_client
    SSE_AVAILABLE = True
except ImportError:
    SSE_AVAILABLE = False

try:
    from mcp.client.streamable_http import streamablehttp_client
    STREAMABLE_HTTP_AVAILABLE = True
except ImportError:
    STREAMABLE_HTTP_AVAILABLE = False


class MCPServerInfo:
    """单个 MCP Server 的连接信息"""

    def __init__(self, name: str, session=None):
        self.name = name
        self.session = session
        self.tools: list = []
        self.connected = False
        self.error = ""
        self._exit_stack: Optional[contextlib.AsyncExitStack] = None


class MCPManager:
    """管理多个 MCP Server 的连接和工具调用"""

    def __init__(self):
        self.servers: Dict[str, MCPServerInfo] = {}
        self._stdio_exit_stack = contextlib.AsyncExitStack()
        self._project_root = ""
        self._all_configs: Dict[str, dict] = {}
        self._disabled_servers: set = set()

    async def connect_all(self, mcp_config: dict, project_root: str = ""):
        """根据配置连接所有 MCP Server

        SSE/HTTP 连接必须在调用者任务中初始化（anyio cancel scope 要求），
        因此只有 stdio 类型才能用 asyncio.gather 并发启动。
        """
        self._project_root = project_root
        self._all_configs = dict(mcp_config)

        if not MCP_AVAILABLE:
            logger.error("MCP SDK 未安装，跳过所有 MCP 连接")
            return

        stdio_tasks = []
        remote_servers = []

        for name, cfg in mcp_config.items():
            if not cfg.get("enabled", True):
                continue
            server_type = cfg.get("type", "local")
            if server_type in ("sse", "streamableHttp", "streamable_http"):
                remote_servers.append((name, cfg))
            else:
                stdio_tasks.append(self.connect_server(name, cfg))

        if stdio_tasks:
            await asyncio.gather(*stdio_tasks, return_exceptions=True)

        for name, cfg in remote_servers:
            await self.connect_server(name, cfg)

    async def connect_server(self, name: str, cfg: dict):
        """连接单个 MCP Server"""
        if not MCP_AVAILABLE:
            return

        info = MCPServerInfo(name)
        self.servers[name] = info
        server_type = cfg.get("type", "local")

        try:
            if server_type in ("sse",):
                await self._connect_sse(name, cfg, info)
            elif server_type in ("streamableHttp", "streamable_http"):
                await self._connect_streamable_http(name, cfg, info)
            else:
                await self._connect_stdio(name, cfg, info)

            logger.info(f"MCP [{name}] 已连接 ({server_type})，{len(info.tools)} 个工具")

        except asyncio.TimeoutError:
            info.error = "连接超时"
            logger.error(f"MCP [{name}] 连接超时")
            await self._cleanup_remote(info)
        except FileNotFoundError as e:
            info.error = f"命令未找到: {e}"
            logger.error(f"MCP [{name}] {info.error}")
        except BaseException as e:
            if isinstance(e, BaseExceptionGroup):
                msgs = [f"{type(se).__name__}: {se}" for se in e.exceptions]
                info.error = "; ".join(msgs)
            else:
                info.error = f"{type(e).__name__}: {e}"
            logger.error(f"MCP [{name}] 连接失败: {info.error}")
            await self._cleanup_remote(info)

    @staticmethod
    async def _cleanup_remote(info: MCPServerInfo):
        if info._exit_stack is not None:
            try:
                await info._exit_stack.aclose()
            except (Exception, BaseException):
                pass
            info._exit_stack = None

    async def _connect_stdio(self, name: str, cfg: dict, info: MCPServerInfo):
        command = cfg.get("command", [])
        if isinstance(command, str):
            command = [command]
        args = cfg.get("args", [])
        full_command = command + args
        if not full_command:
            info.error = "未配置 command"
            return

        custom_env = cfg.get("environment", {})
        merged_env = {**os.environ, **custom_env} if custom_env else None
        cwd = cfg.get("cwd", self._project_root or None)

        server_params = StdioServerParameters(
            command=full_command[0],
            args=full_command[1:] if len(full_command) > 1 else [],
            env=merged_env,
            cwd=cwd,
        )

        transport = stdio_client(server_params)
        streams = await self._stdio_exit_stack.enter_async_context(transport)
        session = ClientSession(*streams)
        await self._stdio_exit_stack.enter_async_context(session)

        init_timeout = cfg.get("init_timeout", 60)
        await asyncio.wait_for(session.initialize(), timeout=init_timeout)

        tools_result = await asyncio.wait_for(session.list_tools(), timeout=30)
        info.session = session
        info.tools = tools_result.tools if tools_result.tools else []
        info.connected = True

    async def _connect_sse(self, name: str, cfg: dict, info: MCPServerInfo):
        if not SSE_AVAILABLE:
            info.error = "mcp SSE 客户端不可用，请升级: pip install mcp[sse]"
            return

        url = cfg.get("url", "")
        if not url:
            info.error = "SSE 类型需要配置 url"
            return

        headers = cfg.get("headers", {})
        exit_stack = contextlib.AsyncExitStack()
        info._exit_stack = exit_stack

        transport = sse_client(url=url, headers=headers)
        streams = await exit_stack.enter_async_context(transport)
        session = ClientSession(*streams)
        await exit_stack.enter_async_context(session)

        init_timeout = cfg.get("init_timeout", 30)
        await asyncio.wait_for(session.initialize(), timeout=init_timeout)

        tools_result = await asyncio.wait_for(session.list_tools(), timeout=30)
        info.session = session
        info.tools = tools_result.tools if tools_result.tools else []
        info.connected = True

    async def _connect_streamable_http(self, name: str, cfg: dict, info: MCPServerInfo):
        if not STREAMABLE_HTTP_AVAILABLE:
            info.error = "mcp Streamable HTTP 客户端不可用，请升级: pip install mcp"
            return

        url = cfg.get("url", "") or cfg.get("baseUrl", "")
        if not url:
            info.error = "streamableHttp 类型需要配置 url 或 baseUrl"
            return

        headers = cfg.get("headers", {})
        exit_stack = contextlib.AsyncExitStack()
        info._exit_stack = exit_stack

        transport = streamablehttp_client(url=url, headers=headers)
        streams = await exit_stack.enter_async_context(transport)
        read_stream, write_stream = streams[0], streams[1]
        session = ClientSession(read_stream, write_stream)
        await exit_stack.enter_async_context(session)

        init_timeout = cfg.get("init_timeout", 30)
        await asyncio.wait_for(session.initialize(), timeout=init_timeout)

        tools_result = await asyncio.wait_for(session.list_tools(), timeout=30)
        info.session = session
        info.tools = tools_result.tools if tools_result.tools else []
        info.connected = True

    async def disconnect_all(self):
        try:
            await self._stdio_exit_stack.aclose()
        except (Exception, BaseException):
            pass
        self._stdio_exit_stack = contextlib.AsyncExitStack()

        for info in self.servers.values():
            if info._exit_stack is not None:
                try:
                    await info._exit_stack.aclose()
                except (Exception, BaseException):
                    pass
                info._exit_stack = None

        self.servers.clear()

    def toggle_server(self, name: str) -> bool:
        if name in self._disabled_servers:
            self._disabled_servers.discard(name)
            return True
        else:
            self._disabled_servers.add(name)
            return False

    def is_server_disabled(self, name: str) -> bool:
        return name in self._disabled_servers

    def get_all_tools_openai_format(self) -> List[dict]:
        tools = []
        for server_name, info in self.servers.items():
            if not info.connected or server_name in self._disabled_servers:
                continue
            for t in info.tools:
                input_schema = {}
                if hasattr(t, 'inputSchema') and t.inputSchema:
                    input_schema = t.inputSchema
                elif hasattr(t, 'input_schema') and t.input_schema:
                    input_schema = t.input_schema

                tools.append({
                    "type": "function",
                    "function": {
                        "name": f"mcp__{server_name}__{t.name}",
                        "description": f"[MCP:{server_name}] {t.description or t.name}",
                        "parameters": input_schema,
                    },
                })
        return tools

    def get_tool_info_list(self) -> List[dict]:
        result = []
        for server_name, info in self.servers.items():
            if not info.connected or server_name in self._disabled_servers:
                continue
            for t in info.tools:
                result.append({
                    "name": t.name,
                    "server": server_name,
                    "description": t.description or "",
                })
        return result

    def get_server_status(self) -> List[dict]:
        result = []
        seen = set()
        for name, info in self.servers.items():
            seen.add(name)
            result.append({
                "name": name,
                "connected": info.connected,
                "tools_count": len(info.tools),
                "error": info.error,
                "disabled": name in self._disabled_servers,
                "config_disabled": False,
            })
        for name, cfg in self._all_configs.items():
            if name not in seen and not cfg.get("enabled", True):
                result.append({
                    "name": name,
                    "connected": False,
                    "tools_count": 0,
                    "error": "",
                    "disabled": False,
                    "config_disabled": True,
                })
        return result

    async def call_tool(self, full_tool_name: str, arguments: dict) -> str:
        """调用 MCP 工具。full_tool_name 格式: mcp__{server}__{tool}"""
        parts = full_tool_name.split("__", 2)
        if len(parts) != 3 or parts[0] != "mcp":
            return f"[错误] 无效的 MCP 工具名: {full_tool_name}"

        server_name = parts[1]
        tool_name = parts[2]

        if server_name in self._disabled_servers:
            return f"[已拦截] MCP Server '{server_name}' 已被禁用"

        info = self.servers.get(server_name)
        if not info or not info.connected or not info.session:
            return f"[错误] MCP Server '{server_name}' 未连接"

        try:
            result = await asyncio.wait_for(
                info.session.call_tool(tool_name, arguments=arguments),
                timeout=60,
            )

            texts = []
            for item in result.content:
                if hasattr(item, 'text'):
                    texts.append(item.text)
                elif hasattr(item, 'data'):
                    texts.append(str(item.data))
                else:
                    texts.append(str(item))

            return "\n".join(texts) if texts else "(空结果)"

        except asyncio.TimeoutError:
            return f"[超时] MCP 工具 {tool_name} 执行超时(60s)"
        except Exception as e:
            return f"[错误] MCP 工具调用失败: {type(e).__name__}: {e}"

    def is_mcp_tool(self, tool_name: str) -> bool:
        return tool_name.startswith("mcp__")

`````

--- **end of file: nb_agent/mcp/client.py** (project: nb_agent) --- 

---


--- **start of file: nb_agent/mcp/__init__.py** (project: nb_agent) --- 


### 📄 Python File Metadata: `nb_agent/mcp/__init__.py`

#### 📦 Imports

- `from client import MCPManager`


---

`````python
from .client import MCPManager  # noqa: F401

`````

--- **end of file: nb_agent/mcp/__init__.py** (project: nb_agent) --- 

---


--- **start of file: nb_agent/session/models.py** (project: nb_agent) --- 


### 📄 Python File Metadata: `nb_agent/session/models.py`

#### 📝 Module Docstring

`````
SQLModel 数据模型 — 会话和消息
`````

#### 📦 Imports

- `from typing import Optional`
- `from sqlmodel import SQLModel`
- `from sqlmodel import Field`

#### 🏛️ Classes (2)

##### 📌 `class ChatSession(SQLModel)`
*Line: 7*

**Class Variables (6):**
- `__tablename__ = 'sessions'`
- `id: str = Field(primary_key=True)`
- `title: str = Field(default='')`
- `model_id: str = Field(default='')`
- `created_at: str = Field(default='')`
- `updated_at: str = Field(default='')`

##### 📌 `class Message(SQLModel)`
*Line: 17*

**Class Variables (8):**
- `__tablename__ = 'messages'`
- `id: Optional[int] = Field(default=None, primary_key=True)`
- `session_id: str = Field(index=True)`
- `role: str = Field(default='')`
- `content: str = Field(default='')`
- `reasoning: str = Field(default='')`
- `tool_calls_json: str = Field(default='[]')`
- `created_at: str = Field(default='')`


---

`````python
"""SQLModel 数据模型 — 会话和消息"""

from typing import Optional
from sqlmodel import SQLModel, Field


class ChatSession(SQLModel, table=True):
    __tablename__ = "sessions"

    id: str = Field(primary_key=True)
    title: str = Field(default="")
    model_id: str = Field(default="")
    created_at: str = Field(default="")
    updated_at: str = Field(default="")


class Message(SQLModel, table=True):
    __tablename__ = "messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(index=True)
    role: str = Field(default="")
    content: str = Field(default="")
    reasoning: str = Field(default="")
    tool_calls_json: str = Field(default="[]")
    created_at: str = Field(default="")

`````

--- **end of file: nb_agent/session/models.py** (project: nb_agent) --- 

---


--- **start of file: nb_agent/session/store.py** (project: nb_agent) --- 


### 📄 Python File Metadata: `nb_agent/session/store.py`

#### 📝 Module Docstring

`````
会话持久化 — SQLModel ORM，默认 SQLite，可切换 PostgreSQL
`````

#### 📦 Imports

- `import json`
- `import os`
- `import datetime`
- `from pathlib import Path`
- `from typing import List`
- `from typing import Dict`
- `from typing import Optional`
- `from sqlmodel import SQLModel`
- `from sqlmodel import Session`
- `from sqlmodel import create_engine`
- `from sqlmodel import select`
- `from models import ChatSession`
- `from models import Message`

#### 🏛️ Classes (1)

##### 📌 `class SessionStore`
*Line: 14*

**🔧 Constructor (`__init__`):**
- `def __init__(self, db_path: str = '')`
  - **Parameters:**
    - `self`
    - `db_path: str = ''`

**Public Methods (7):**
- `def create_session(self, session_id: str, title: str = '', model_id: str = '') -> str`
- `def get_session_title(self, session_id: str) -> str`
- `def update_session_title(self, session_id: str, title: str)`
- `def list_sessions(self, limit: int = 50) -> List[dict]`
- `def save_message(self, session_id: str, role: str, content: str, reasoning: str = '', tool_calls: Optional[list] = None)`
- `def get_messages(self, session_id: str) -> List[Dict]`
- `def delete_session(self, session_id: str)`


---

`````python
"""会话持久化 — SQLModel ORM，默认 SQLite，可切换 PostgreSQL"""

import json
import os
import datetime
from pathlib import Path
from typing import List, Dict, Optional

from sqlmodel import SQLModel, Session, create_engine, select

from .models import ChatSession, Message


class SessionStore:

    def __init__(self, db_path: str = ""):
        if not db_path:
            db_dir = os.path.join(Path.home(), ".nb_agent")
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, "sessions.db")

        db_path = os.path.expanduser(db_path)
        parent = os.path.dirname(db_path)
        if parent:
            os.makedirs(parent, exist_ok=True)

        if db_path.startswith("postgresql"):
            self._url = db_path
        else:
            self._url = f"sqlite:///{db_path}"

        connect_args = {}
        if self._url.startswith("sqlite"):
            connect_args["check_same_thread"] = False

        self._engine = create_engine(self._url, connect_args=connect_args)
        SQLModel.metadata.create_all(self._engine)

    def _session(self) -> Session:
        return Session(self._engine)

    def create_session(self, session_id: str, title: str = "", model_id: str = "") -> str:
        now = datetime.datetime.now().isoformat()
        with self._session() as s:
            s.add(ChatSession(
                id=session_id, title=title, model_id=model_id,
                created_at=now, updated_at=now,
            ))
            s.commit()
        return session_id

    def get_session_title(self, session_id: str) -> str:
        with self._session() as s:
            row = s.get(ChatSession, session_id)
            return row.title if row else ""

    def update_session_title(self, session_id: str, title: str):
        now = datetime.datetime.now().isoformat()
        with self._session() as s:
            row = s.get(ChatSession, session_id)
            if row:
                row.title = title
                row.updated_at = now
                s.add(row)
                s.commit()

    def list_sessions(self, limit: int = 50) -> List[dict]:
        with self._session() as s:
            stmt = select(ChatSession).order_by(ChatSession.updated_at.desc()).limit(limit)
            rows = s.exec(stmt).all()
            return [r.model_dump() for r in rows]

    def save_message(self, session_id: str, role: str, content: str,
                     reasoning: str = "", tool_calls: Optional[list] = None):
        now = datetime.datetime.now().isoformat()
        tc_json = json.dumps(tool_calls or [], ensure_ascii=False)
        with self._session() as s:
            s.add(Message(
                session_id=session_id, role=role, content=content,
                reasoning=reasoning, tool_calls_json=tc_json, created_at=now,
            ))
            row = s.get(ChatSession, session_id)
            if row:
                row.updated_at = now
                s.add(row)
            s.commit()

    def get_messages(self, session_id: str) -> List[Dict]:
        with self._session() as s:
            stmt = (
                select(Message)
                .where(Message.session_id == session_id)
                .order_by(Message.id)
            )
            rows = s.exec(stmt).all()
            return [
                {
                    "role": r.role,
                    "content": r.content,
                    "reasoning": r.reasoning,
                    "tool_calls_json": r.tool_calls_json,
                }
                for r in rows
            ]

    def delete_session(self, session_id: str):
        with self._session() as s:
            stmt = select(Message).where(Message.session_id == session_id)
            for msg in s.exec(stmt).all():
                s.delete(msg)
            row = s.get(ChatSession, session_id)
            if row:
                s.delete(row)
            s.commit()

`````

--- **end of file: nb_agent/session/store.py** (project: nb_agent) --- 

---


--- **start of file: nb_agent/session/__init__.py** (project: nb_agent) --- 


### 📄 Python File Metadata: `nb_agent/session/__init__.py`

#### 📦 Imports

- `from store import SessionStore`


---

`````python
from .store import SessionStore  # noqa: F401

`````

--- **end of file: nb_agent/session/__init__.py** (project: nb_agent) --- 

---


--- **start of file: nb_agent/skills/manager.py** (project: nb_agent) --- 


### 📄 Python File Metadata: `nb_agent/skills/manager.py`

#### 📝 Module Docstring

`````
SkillManager — 发现、加载与匹配 SKILL.md 技能文档。
`````

#### 📦 Imports

- `from __future__ import annotations`
- `import fnmatch`
- `import re`
- `from dataclasses import dataclass`
- `from pathlib import Path`
- `from typing import Any`
- `import yaml`

#### 🏛️ Classes (2)

##### 📌 `class SkillRecord`
*Line: 27*

**Class Variables (6):**
- `name: str`
- `description: str`
- `paths: tuple[str, ...]`
- `skill_path: Path`
- `source: str`
- `disable_model_invocation: bool = False`

##### 📌 `class SkillManager`
*Line: 128*

**Docstring:**
`````
Manage progressive disclosure of SKILL.md instructions.
`````

**🔧 Constructor (`__init__`):**
- `def __init__(self, project_root: Path | None = None)`
  - **Parameters:**
    - `self`
    - `project_root: Path | None = None`

**Public Methods (6):**
- `def discover(self) -> None`
  - *Scan builtin, global, cross-platform, and project skill directories.*
- `def get_manifest(self) -> list[dict[str, str]]`
  - *Return auto-invocable skills (exclude disable-model-invocation=true).*
- `def get_all_skills(self) -> list[dict[str, str]]`
  - *Return all skills including manual-only ones.*
- `def view_skill(self, skill_name: str) -> dict[str, Any]`
  - *Load the full SKILL.md content for a skill.*
- `def match_skills(self, file_paths: list[str]) -> list[str]`
  - *Return skill names whose ``paths`` globs match any given file path.*
- `def get_view_skill_schema(self) -> dict[str, Any]`
  - *Return the OpenAI function schema for the ``view_skill`` tool.*


---

`````python
"""SkillManager — 发现、加载与匹配 SKILL.md 技能文档。"""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

_BUILTIN_DIR = Path(__file__).resolve().parent / "builtin"

_GLOBAL_DIRS = [
    Path.home() / ".nb_agent" / "skills",
    Path.home() / ".agents" / "skills",
]

_PROJECT_DIR_NAMES = [
    Path(".nb_agent") / "skills",
    Path(".agents") / "skills",
]


@dataclass(frozen=True)
class SkillRecord:
    name: str
    description: str
    paths: tuple[str, ...]
    skill_path: Path
    source: str
    disable_model_invocation: bool = False


def _split_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter separated by ``---`` from markdown body."""
    text = content.lstrip("\ufeff")
    if not text.startswith("---"):
        return {}, text

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text

    metadata = yaml.safe_load(parts[1]) or {}
    if not isinstance(metadata, dict):
        metadata = {}
    body = parts[2].lstrip("\n")
    return metadata, body


def _read_frontmatter(skill_path: Path) -> dict[str, Any]:
    try:
        content = skill_path.read_text(encoding="utf-8")
    except OSError:
        return {}
    metadata, _ = _split_frontmatter(content)
    return metadata


def _normalize_paths(raw_paths: Any) -> tuple[str, ...]:
    if raw_paths is None:
        return ()
    if isinstance(raw_paths, str):
        items = [part.strip() for part in raw_paths.split(",")]
    elif isinstance(raw_paths, list):
        items = [str(part).strip() for part in raw_paths]
    else:
        return ()
    return tuple(item for item in items if item)


def _glob_to_regex(pattern: str) -> re.Pattern[str]:
    normalized = pattern.replace("\\", "/")
    parts: list[str] = []
    i = 0
    while i < len(normalized):
        char = normalized[i]
        if char == "*":
            if i + 1 < len(normalized) and normalized[i + 1] == "*":
                parts.append(".*")
                i += 2
                if i < len(normalized) and normalized[i] == "/":
                    i += 1
                continue
            parts.append("[^/]*")
            i += 1
            continue
        if char == "?":
            parts.append("[^/]")
        else:
            parts.append(re.escape(char))
        i += 1
    return re.compile(f"^{''.join(parts)}$")


def _path_matches_glob(file_path: str, pattern: str) -> bool:
    normalized_path = file_path.replace("\\", "/").lstrip("./")
    normalized_pattern = pattern.replace("\\", "/").lstrip("./")
    if not normalized_path or not normalized_pattern:
        return False

    path = Path(normalized_path)
    if path.match(normalized_pattern):
        return True

    if normalized_pattern.startswith("**/"):
        suffix = normalized_pattern[3:]
        if fnmatch.fnmatch(path.name, suffix):
            return True

    if "**" in normalized_pattern or "/" in normalized_pattern:
        return bool(_glob_to_regex(normalized_pattern).fullmatch(normalized_path))

    return fnmatch.fnmatch(path.name, normalized_pattern) or fnmatch.fnmatch(
        normalized_path,
        normalized_pattern,
    )


def _iter_skill_files(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(path for path in root.glob("*/SKILL.md") if path.is_file())


class SkillManager:
    """Manage progressive disclosure of SKILL.md instructions."""

    def __init__(self, project_root: Path | None = None) -> None:
        self._project_root = project_root or Path.cwd()
        self._skills: dict[str, SkillRecord] = {}

    def discover(self) -> None:
        """Scan builtin, global, cross-platform, and project skill directories."""
        discovered: dict[str, SkillRecord] = {}

        scan_targets: list[tuple[str, Path]] = [("builtin", _BUILTIN_DIR)]
        for gdir in _GLOBAL_DIRS:
            scan_targets.append(("global", gdir))
        for pdir_name in _PROJECT_DIR_NAMES:
            scan_targets.append(("project", self._project_root / pdir_name))

        for source, root in scan_targets:
            for skill_path in _iter_skill_files(root):
                metadata = _read_frontmatter(skill_path)
                name = metadata.get("name")
                if not isinstance(name, str) or not name.strip():
                    continue

                description = metadata.get("description", "")
                if not isinstance(description, str):
                    description = str(description)

                dmi = metadata.get("disable-model-invocation", False)
                if not isinstance(dmi, bool):
                    dmi = str(dmi).lower() in ("true", "1", "yes")

                record = SkillRecord(
                    name=name.strip(),
                    description=description.strip(),
                    paths=_normalize_paths(metadata.get("paths")),
                    skill_path=skill_path,
                    source=source,
                    disable_model_invocation=dmi,
                )
                discovered[record.name] = record

        self._skills = discovered

    def get_manifest(self) -> list[dict[str, str]]:
        """Return auto-invocable skills (exclude disable-model-invocation=true)."""
        return [
            {"name": record.name, "description": record.description}
            for record in sorted(self._skills.values(), key=lambda item: item.name)
            if not record.disable_model_invocation
        ]

    def get_all_skills(self) -> list[dict[str, str]]:
        """Return all skills including manual-only ones."""
        return [
            {
                "name": record.name,
                "description": record.description,
                "manual_only": record.disable_model_invocation,
            }
            for record in sorted(self._skills.values(), key=lambda item: item.name)
        ]

    def view_skill(self, skill_name: str) -> dict[str, Any]:
        """Load the full SKILL.md content for a skill."""
        record = self._skills.get(skill_name)
        if record is None:
            return {
                "success": False,
                "error": f"Skill '{skill_name}' not found.",
                "available_skills": sorted(self._skills),
            }

        try:
            raw_content = record.skill_path.read_text(encoding="utf-8")
        except OSError as exc:
            return {
                "success": False,
                "error": f"Failed to read skill '{skill_name}': {exc}",
            }

        metadata, body = _split_frontmatter(raw_content)
        return {
            "success": True,
            "name": record.name,
            "description": record.description,
            "paths": list(record.paths),
            "source": record.source,
            "skill_path": str(record.skill_path),
            "content": body.strip(),
            "raw_content": raw_content,
            "metadata": metadata,
        }

    def match_skills(self, file_paths: list[str]) -> list[str]:
        """Return skill names whose ``paths`` globs match any given file path."""
        if not file_paths:
            return []

        matched: list[str] = []
        for record in sorted(self._skills.values(), key=lambda item: item.name):
            if not record.paths:
                continue
            if any(
                _path_matches_glob(file_path, pattern)
                for file_path in file_paths
                for pattern in record.paths
            ):
                matched.append(record.name)
        return matched

    def get_view_skill_schema(self) -> dict[str, Any]:
        """Return the OpenAI function schema for the ``view_skill`` tool."""
        return {
            "type": "function",
            "function": {
                "name": "view_skill",
                "description": (
                    "Load the full instructions for a skill by name. "
                    "Use this when a task matches a skill listed in the manifest."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "skill_name": {
                            "type": "string",
                            "description": "The skill name from the manifest.",
                        }
                    },
                    "required": ["skill_name"],
                },
            },
        }

`````

--- **end of file: nb_agent/skills/manager.py** (project: nb_agent) --- 

---


--- **start of file: nb_agent/skills/__init__.py** (project: nb_agent) --- 


### 📄 Python File Metadata: `nb_agent/skills/__init__.py`

#### 📝 Module Docstring

`````
Skills 系统 — 渐进式披露 SKILL.md 指令。
`````

#### 📦 Imports

- `from manager import SkillManager`


---

`````python
"""Skills 系统 — 渐进式披露 SKILL.md 指令。"""

from .manager import SkillManager

__all__ = ["SkillManager"]

`````

--- **end of file: nb_agent/skills/__init__.py** (project: nb_agent) --- 

---


--- **start of file: nb_agent/skills/builtin/code-review/SKILL.md** (project: nb_agent) --- 

`````markdown
---
name: code-review
description: >-
  审查代码质量、安全性和最佳实践。当用户请求代码审查、review PR、
  检查代码变更、或提到"帮我看看这段代码"时使用。
paths: "**/*.py,**/*.ts,**/*.tsx,**/*.js,**/*.jsx,**/*.go,**/*.rs"
---

# 代码审查 Skill

在审查代码时，按以下流程系统性地评估变更，而不是逐行扫读。

## 审查流程

1. **理解意图**：先确认这次变更要解决什么问题，再判断实现是否匹配目标。
2. **阅读范围**：优先看 diff 和调用链，必要时扩展到相关测试与配置文件。
3. **分层检查**：按严重程度归类问题，避免把风格偏好当成缺陷。
4. **给出结论**：总结风险、阻塞项、建议项，并指出验证方式。

## 检查维度

### 正确性

- 边界条件、空值、异常路径是否处理完整
- 并发、异步、重试、幂等是否会导致竞态或重复副作用
- 类型、返回值、错误码是否与调用方约定一致

### 安全性

- 是否存在注入、路径穿越、权限绕过、敏感信息泄露
- 外部输入是否经过校验与规范化
- 密钥、token、凭据是否硬编码或写入日志

### 可维护性

- 命名是否表达意图，函数是否职责单一
- 是否存在重复逻辑，能否复用现有抽象
- 注释是否解释“为什么”，而不是复述代码

### 性能

- 是否存在 N+1 查询、无界循环、重复计算
- 热路径上是否引入不必要的 I/O 或分配
- 缓存、批处理、索引使用是否合理

### 测试

- 是否覆盖新增逻辑的主路径与失败路径
- 测试是否稳定、可读，避免依赖真实外部服务
- 回归风险高的区域是否缺少断言

## 输出格式

按以下结构回复：

```markdown
## 总结
<1-2 句话概括整体质量与是否建议合并>

## 阻塞问题
- [严重] <问题> — <位置> — <原因> — <修复建议>

## 建议改进
- [建议] <问题> — <位置> — <原因> — <修复建议>

## 亮点
- <值得保留的设计或实现>

## 测试建议
- <需要补充或执行的验证>
```

## 审查原则

- 先找真实风险，再谈风格优化
- 每个问题都要给出具体位置和可执行建议
- 没有发现问题时明确说明，并列出已检查的关键面
- 区分“必须修复”和“可以后续优化”
- 尊重项目现有约定，不强行引入新风格

`````

--- **end of file: nb_agent/skills/builtin/code-review/SKILL.md** (project: nb_agent) --- 

---


--- **start of file: nb_agent/skills/builtin/explain-code/SKILL.md** (project: nb_agent) --- 

`````markdown
---
name: explain-code
description: >-
  清晰解释代码结构、数据流和执行逻辑。当用户询问"这段代码做什么"、
  "帮我看看这个函数"、"解释一下这个模块"、或需要理解调用链时使用。
paths: "**/*"
---

# 代码解释 Skill

在解释代码时，目标是让读者快速建立 mental model，而不是复述每一行语法。

## 解释流程

1. **定位入口**：指出用户关心的文件、函数、类或调用链起点。
2. **概括职责**：用一句话说明“这段代码是做什么的”。
3. **展开结构**：按模块、层次或执行顺序组织说明。
4. **追踪数据流**：说明输入如何变成输出，关键状态在哪里变化。
5. **点明边界**：说明依赖、副作用、失败路径和隐含假设。

## 讲解层次

### 第一层：概览

- 这段代码解决什么问题
- 在系统中的位置（入口、服务、工具、中间层等）
- 最重要的 3 个概念或组件

### 第二层：执行路径

- 正常流程分几步
- 谁调用谁，关键分支在哪里
- 异步、回调、事件、消息如何传递

### 第三层：实现细节

- 重要算法、协议、数据结构
- 非显而易见的业务规则
- 与框架/库相关的关键用法

## 输出格式

默认使用以下结构：

```markdown
## 这段代码做什么
<一句话概述>

## 核心组件
- `<组件>` — <职责>

## 执行流程
1. <步骤>
2. <步骤>

## 数据如何流动
<输入 -> 处理 -> 输出>

## 需要注意的点
- <边界条件 / 副作用 / 依赖>

## 如果想继续深入
- <可选的下一步阅读位置>
```

## 讲解原则

- 先整体后局部，先目的后实现
- 使用与源码一致的命名，避免发明新术语
- 复杂逻辑优先用步骤列表或简短伪代码
- 对初学者友好，但不牺牲准确性
- 如果上下文不足，明确说明假设，而不是猜测
- 仅在有助于理解时使用类比、表格或 ASCII 图

## 常见场景

### 解释单个函数

说明参数含义、返回值、副作用、异常和典型调用方式。

### 解释模块或文件

说明模块边界、对外 API、内部协作关系和主要扩展点。

### 解释调用链

从入口到最终结果，按时间顺序说明每一跳做了什么。

### 解释配置或框架胶水代码

重点说明“为什么需要它”以及“删掉/改错会怎样”。

`````

--- **end of file: nb_agent/skills/builtin/explain-code/SKILL.md** (project: nb_agent) --- 

---


--- **start of file: nb_agent/skills/builtin/refactor/SKILL.md** (project: nb_agent) --- 

`````markdown
---
name: refactor
description: >-
  安全地重构代码，保持行为不变并降低复杂度。当用户请求重构、
  优化代码结构、消除重复、简化复杂逻辑、或提到"帮我整理一下代码"时使用。
paths: "**/*.py,**/*.ts,**/*.tsx,**/*.js,**/*.jsx,**/*.go,**/*.rs"
---

# 代码重构 Skill

重构的目标是在不改变外部行为的前提下，提高可读性、可测试性和可维护性。

## 重构流程

1. **确认行为基线**：明确当前功能、公共 API、边界条件与现有测试覆盖。
2. **识别坏味道**：重复、过长函数、深层嵌套、隐式依赖、命名误导等。
3. **选择最小步骤**：每次只做一种重构，便于 review 和回滚。
4. **保持测试绿**：每步完成后运行相关测试；没有测试时先补关键路径测试。
5. **验证等价性**：确认输入输出、副作用、错误处理与重构前一致。

## 适用重构手法

### 结构整理

- 提取函数 / 提取变量
- 内联过度抽象的薄封装
- 拆分大类，按职责划分子模块
- 用早返回减少嵌套

### 依赖治理

- 依赖注入替代硬编码全局状态
- 收敛重复配置与 magic number
- 将副作用与纯逻辑分离

### 接口稳定

- 优先保留现有公共 API
- 必须变更时提供过渡层或明确迁移说明
- 不在同一提交里混入无关功能改动

## 实施原则

- **小步提交**：一个重构意图对应一组清晰变更
- **行为优先**：先保证正确，再追求优雅
- **测试先行或测试同行**：没有安全网时不要大改
- **匹配项目风格**：沿用现有命名、目录结构和抽象层级
- **避免过度设计**：不为假想未来引入复杂框架

## 输出格式

重构前先给出计划：

```markdown
## 重构目标
<想改善什么问题>

## 当前问题
- <坏味道 / 风险>

## 计划步骤
1. <小步变更>
2. <小步变更>

## 风险与验证
- 风险: <可能影响的区域>
- 验证: <要运行的测试或检查>
```

重构完成后总结：

```markdown
## 已完成变更
- <具体改动>

## 行为是否保持不变
<是/否，以及依据>

## 后续建议
- <可选的下一步重构>
```

## 禁止事项

- 不要同时做重构和功能开发
- 不要在没有理解调用方的情况下修改公共接口
- 不要删除看起来“多余”的代码，除非确认无引用且无运行时依赖
- 不要为了“更短”牺牲可读性
- 不要引入与项目无关的新依赖

## 何时停止

- 代码已经清晰、测试通过、review 可理解
- 进一步抽象不会明显降低复杂度
- 剩余问题属于产品需求变更，而不是重构范围

`````

--- **end of file: nb_agent/skills/builtin/refactor/SKILL.md** (project: nb_agent) --- 

---


--- **start of file: nb_agent/tools/base.py** (project: nb_agent) --- 


### 📄 Python File Metadata: `nb_agent/tools/base.py`

#### 📝 Module Docstring

`````
工具注册框架 — 基于 Pydantic + 装饰器自动生成 OpenAI Function Calling Schema

用法:
    from nb_agent.tools import tool

    class MyParams(BaseModel):
        query: str = Field(description="搜索关键词")

    # 无分组
    @tool
    def search(params: MyParams) -> str:
        """搜索互联网"""
        ...

    # 有分组 — 注册名变为 file__read_file
    @tool(group="file")
    def read_file(params: ReadParams) -> str:
        """读取文件"""
        ...
`````

#### 📦 Imports

- `import inspect`
- `from typing import Dict`
- `from typing import Callable`
- `from typing import Optional`
- `from typing import Type`
- `from typing import get_type_hints`
- `from pydantic import BaseModel`

#### 🔧 Public Functions (2)

- `def tool(func = None)`
  - *Line: 131*
  - **Docstring:**
  `````
  装饰器：自动注册工具函数到 TOOL_REGISTRY
  
  用法:
      @tool                          # 无分组，注册名 = func_name
      @tool(group="file")            # 有分组，注册名 = file__func_name
  `````

- `def decorator(fn)`
  - *Line: 140*


---

`````python
"""
工具注册框架 — 基于 Pydantic + 装饰器自动生成 OpenAI Function Calling Schema

用法:
    from nb_agent.tools import tool

    class MyParams(BaseModel):
        query: str = Field(description="搜索关键词")

    # 无分组
    @tool
    def search(params: MyParams) -> str:
        \"\"\"搜索互联网\"\"\"
        ...

    # 有分组 — 注册名变为 file__read_file
    @tool(group="file")
    def read_file(params: ReadParams) -> str:
        \"\"\"读取文件\"\"\"
        ...
"""

import inspect
from typing import Dict, Callable, Optional, Type, get_type_hints

from pydantic import BaseModel


TOOL_REGISTRY: Dict[str, dict] = {}


def _pydantic_schema_to_openai_params(model_cls: Type[BaseModel]) -> dict:
    """将 Pydantic model 的 JSON Schema 转换为 OpenAI function parameters 格式"""
    raw_schema = model_cls.model_json_schema()

    properties = {}
    required = []

    for name, field_schema in raw_schema.get("properties", {}).items():
        prop = {}
        field_type = field_schema.get("type")
        if field_type:
            prop["type"] = field_type
            if field_type == "array" and "items" in field_schema:
                prop["items"] = field_schema["items"]
        else:
            prop["type"] = "string"

        if "description" in field_schema:
            prop["description"] = field_schema["description"]

        if "anyOf" in field_schema:
            for variant in field_schema["anyOf"]:
                vtype = variant.get("type")
                if vtype and vtype != "null":
                    prop["type"] = vtype
                    if vtype == "array" and "items" in variant:
                        prop["items"] = variant["items"]
                    break

        if "enum" in field_schema:
            prop["enum"] = field_schema["enum"]

        if "default" in field_schema:
            prop["default"] = field_schema["default"]

        properties[name] = prop

    for name in raw_schema.get("required", []):
        required.append(name)

    return {
        "type": "object",
        "properties": properties,
        "required": required,
    }


def _find_model_cls(func: Callable) -> Optional[Type[BaseModel]]:
    """从函数签名中查找 Pydantic BaseModel 参数类型"""
    try:
        hints = get_type_hints(func)
    except Exception:
        hints = {}

    sig = inspect.signature(func)
    for param_name, param in sig.parameters.items():
        annotation = hints.get(param_name, param.annotation)
        if annotation is inspect.Parameter.empty:
            continue
        if isinstance(annotation, type) and issubclass(annotation, BaseModel):
            return annotation
    return None


def _register_tool(func: Callable, group: Optional[str] = None) -> Callable:
    """核心注册逻辑：解析函数签名，生成 schema，写入 TOOL_REGISTRY"""
    model_cls = _find_model_cls(func)
    if model_cls is None:
        raise TypeError(
            f"工具函数 '{func.__name__}' 必须有一个 Pydantic BaseModel 参数。"
            f"示例: def my_tool(params: MyParams) -> str: ..."
        )

    description = (func.__doc__ or "").strip()
    if not description:
        raise ValueError(f"工具函数 '{func.__name__}' 必须有 docstring 作为工具描述")

    openai_params = _pydantic_schema_to_openai_params(model_cls)
    func_name = func.__name__
    tool_name = f"{group}__{func_name}" if group else func_name

    TOOL_REGISTRY[tool_name] = {
        "function": func,
        "model_cls": model_cls,
        "group": group or "",
        "func_name": func_name,
        "schema": {
            "type": "function",
            "function": {
                "name": tool_name,
                "description": description,
                "parameters": openai_params,
            },
        },
    }

    return func


def tool(func=None, *, group=None):
    """装饰器：自动注册工具函数到 TOOL_REGISTRY

    用法:
        @tool                          # 无分组，注册名 = func_name
        @tool(group="file")            # 有分组，注册名 = file__func_name
    """
    if func is not None:
        return _register_tool(func)
    def decorator(fn):
        return _register_tool(fn, group=group)
    return decorator

`````

--- **end of file: nb_agent/tools/base.py** (project: nb_agent) --- 

---


--- **start of file: nb_agent/tools/builtin.py** (project: nb_agent) --- 


### 📄 Python File Metadata: `nb_agent/tools/builtin.py`

#### 📝 Module Docstring

`````
内置工具 — 使用 Pydantic + @tool 装饰器自动注册
`````

#### 📦 Imports

- `import datetime`
- `from pydantic import BaseModel`
- `from pydantic import Field`
- `from base import tool`
- `from zoneinfo import ZoneInfo`
- `import ast`
- `import operator`

#### 🏛️ Classes (2)

##### 📌 `class GetCurrentTimeParams(BaseModel)`
*Line: 13*

**Class Variables (1):**
- `timezone: str = Field(default='Asia/Shanghai', description='时区，默认 Asia/Shanghai')`

##### 📌 `class CalculateParams(BaseModel)`
*Line: 28*

**Class Variables (1):**
- `expression: str = Field(description="数学表达式，如 '2+3*4' 或 '(100-20)/8'")`

#### 🔧 Public Functions (2)

- `def get_current_time(params: GetCurrentTimeParams) -> str` `tool`
  - *Line: 18*
  - *获取当前日期和时间*

- `def calculate(params: CalculateParams) -> str` `tool`
  - *Line: 33*
  - *计算数学表达式（支持加减乘除、幂运算、取余等）*


---

`````python
"""内置工具 — 使用 Pydantic + @tool 装饰器自动注册"""

import datetime

from pydantic import BaseModel, Field

from .base import tool

from zoneinfo import ZoneInfo



class GetCurrentTimeParams(BaseModel):
    timezone: str = Field(default="Asia/Shanghai", description="时区，默认 Asia/Shanghai")


@tool
def get_current_time(params: GetCurrentTimeParams) -> str:
    """获取当前日期和时间"""
    try:
        tz = ZoneInfo(params.timezone)
    except (KeyError, Exception):
        tz = ZoneInfo("Asia/Shanghai")
    now = datetime.datetime.now(tz)
    return now.strftime(f"%Y-%m-%d %H:%M:%S ({now.strftime('%A')}) [{params.timezone}]")


class CalculateParams(BaseModel):
    expression: str = Field(description="数学表达式，如 '2+3*4' 或 '(100-20)/8'")


@tool
def calculate(params: CalculateParams) -> str:
    """计算数学表达式（支持加减乘除、幂运算、取余等）"""
    import ast
    import operator

    _ops = {
        ast.Add: operator.add, ast.Sub: operator.sub,
        ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod,
        ast.Pow: operator.pow, ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def _safe_eval(node):
        if isinstance(node, ast.Expression):
            return _safe_eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _ops:
            left = _safe_eval(node.left)
            right = _safe_eval(node.right)
            if isinstance(node.op, ast.Pow) and right > 1000:
                raise ValueError("指数过大")
            return _ops[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in _ops:
            return _ops[type(node.op)](_safe_eval(node.operand))
        raise ValueError(f"不支持的表达式: {ast.dump(node)}")

    try:
        tree = ast.parse(params.expression.strip(), mode='eval')
        result = _safe_eval(tree)
        return str(result)
    except ZeroDivisionError:
        return "计算错误: 除以零"
    except Exception as e:
        return f"计算错误: {e}"

`````

--- **end of file: nb_agent/tools/builtin.py** (project: nb_agent) --- 

---


--- **start of file: nb_agent/tools/__init__.py** (project: nb_agent) --- 


### 📄 Python File Metadata: `nb_agent/tools/__init__.py`

#### 📝 Module Docstring

`````
工具模块 — 导入所有工具以触发 @tool 注册，导出 TOOL_REGISTRY
`````

#### 📦 Imports

- `from base import TOOL_REGISTRY`
- `from base import tool`
- `import nb_agent.tools.builtin`


---

`````python
"""工具模块 — 导入所有工具以触发 @tool 注册，导出 TOOL_REGISTRY"""

from .base import TOOL_REGISTRY, tool  # noqa: F401

import nb_agent.tools.builtin  # noqa: F401

`````

--- **end of file: nb_agent/tools/__init__.py** (project: nb_agent) --- 

---


--- **start of file: nb_agent/tui/app.py** (project: nb_agent) --- 


### 📄 Python File Metadata: `nb_agent/tui/app.py`

#### 📝 Module Docstring

`````
TUI 界面 —— 用 Textual 框架构建

布局:
┌─────────────────────────────────────────────────┐
│  nb_agent | deepseek-v4-flash | Tokens: 0       │  ← Header
├──────────────────────────────┬──────────────────-┤
│                              │  已注册工具:      │
│  对话区域（滚动）             │  - get_time      │  ← Main
│                              │  - calculate     │
│  user: 你好                  │                  │
│  model: [流式输出中...]       │  MCP: 未连接      │
│                              │                  │
├──────────────────────────────┴──────────────────-┤
│  > 输入消息...                          [发送]   │  ← Input
│  (Enter=发送, Shift+Enter=换行)                  │
├─────────────────────────────────────────────────┤
│  Tab=模型 | Ctrl+Q=退出 | Ctrl+L=清屏            │  ← Footer
└─────────────────────────────────────────────────┘
`````

#### 📦 Imports

- `import asyncio`
- `import os`
- `import re`
- `import sys`
- `import time`
- `from datetime import datetime`
- `from pathlib import Path`
- `from typing import Optional`
- `from textual.app import App`
- `from textual.app import ComposeResult`
- `from textual.containers import Horizontal`
- `from textual.widgets import Footer`
- `from textual.widgets import Header`
- `from textual.widgets import RichLog`
- `from textual.widgets import Static`
- `from textual.binding import Binding`
- `from textual.screen import ModalScreen`
- `from rich.text import Text`
- `from rich.markdown import Markdown as RichMarkdown`
- `from rich.panel import Panel`
- `from nb_agent.core import AgentCore`
- `from widgets import ChatInput`
- `from widgets import ToolPanel`
- `from widgets import ModelSelectScreen`
- `from widgets import HelpScreen`
- `from widgets import SessionSelectScreen`
- `from widgets import ToolDetailScreen`
- `from widgets import RoundsInputScreen`
- `from widgets import ToolApprovalScreen`
- `from widgets import SkillListScreen`
- `from widgets import SkillContentScreen`
- `from widgets import MentionSelectScreen`
- `from widgets import ToolGroupToggleScreen`
- `from widgets import AgentCommands`
- `from widgets.tool_panel import _fmt_tokens`

#### 🏛️ Classes (1)

##### 📌 `class AgentApp(App)`
*Line: 70*

**Docstring:**
`````
nb_agent TUI 主应用
`````

**🔧 Constructor (`__init__`):**
- `def __init__(self, config: dict)`
  - **Parameters:**
    - `self`
    - `config: dict`

**Public Methods (15):**
- `def compose(self) -> ComposeResult`
- `async def on_mount(self)`
- `def action_stop_ai(self)`
- `def action_edit_last(self)`
- `async def action_send_msg(self)`
- `def action_new_session(self)`
- `def action_resume_session(self)`
- `def action_show_help(self)`
- `def action_toggle_input(self)`
- `def action_show_skills(self)`
- `def action_toggle_tool_groups(self)`
- `def on_chat_input_mention_triggered(self, event: ChatInput.MentionTriggered) -> None`
- `def action_clear_chat(self)`
- `def action_select_model(self)`
- `async def on_unmount(self)`

**Class Variables (4):**
- `TITLE = 'nb_agent'`
- `CSS_PATH = 'styles.tcss'`
- `COMMANDS = App.COMMANDS | {AgentCommands}`
- `BINDINGS = [Binding('ctrl+j', 'send_msg', '发送', show=True, priority=True), Binding('ctrl+k', 'stop_ai', '终止', show=True, priority=True), Binding('ctrl+up', 'edit_last', '编辑上轮', show=True, priority=True), Binding('tab', 'select_model', '模型', show=True, priority=True), Binding('ctrl+n', 'new_session', '新建', show=True, priority=True), Binding('ctrl+r', 'resume_session', '恢复', show=True, priority=True), Binding('ctrl+e', 'toggle_input', '展开', show=True, priority=True), Binding('ctrl+l', 'clear_chat', '清屏', show=True), Binding('f1', 'show_help', '帮助', show=True), Binding('f2', 'show_skills', 'Skills', show=True), Binding('f3', 'toggle_tool_groups', '工具组', show=True), Binding('ctrl+q', 'quit', '退出', show=True, priority=True)]`


---

`````python
"""
TUI 界面 —— 用 Textual 框架构建

布局:
┌─────────────────────────────────────────────────┐
│  nb_agent | deepseek-v4-flash | Tokens: 0       │  ← Header
├──────────────────────────────┬──────────────────-┤
│                              │  已注册工具:      │
│  对话区域（滚动）             │  - get_time      │  ← Main
│                              │  - calculate     │
│  user: 你好                  │                  │
│  model: [流式输出中...]       │  MCP: 未连接      │
│                              │                  │
├──────────────────────────────┴──────────────────-┤
│  > 输入消息...                          [发送]   │  ← Input
│  (Enter=发送, Shift+Enter=换行)                  │
├─────────────────────────────────────────────────┤
│  Tab=模型 | Ctrl+Q=退出 | Ctrl+L=清屏            │  ← Footer
└─────────────────────────────────────────────────┘
"""

import asyncio
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Footer, Header, RichLog, Static
from textual.binding import Binding
from textual.screen import ModalScreen
from rich.text import Text
from rich.markdown import Markdown as RichMarkdown
from rich.panel import Panel

from nb_agent.core import AgentCore
from .widgets import (
    ChatInput,
    ToolPanel,
    ModelSelectScreen,
    HelpScreen,
    SessionSelectScreen,
    ToolDetailScreen,
    RoundsInputScreen,
    ToolApprovalScreen,
    SkillListScreen,
    SkillContentScreen,
    MentionSelectScreen,
    ToolGroupToggleScreen,
    AgentCommands,
)
from .widgets.tool_panel import _fmt_tokens


_SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
_SPINNER_BIG = ["◐", "◓", "◑", "◒"]
_MARQUEE_BASE = "  ◐  AI 正在回答中，请稍候...  按 Ctrl+K 停止  ✦  "
_RAINBOW_COLORS = [
    "#ff0080", "#ff2060", "#ff4040", "#ff6020",
    "#ff8000", "#ffb000", "#ffff00", "#80ff00",
    "#00ff80", "#00ffff", "#0080ff", "#4040ff",
    "#8000ff", "#c000ff", "#ff00ff", "#ff0080",
]


class AgentApp(App):
    """nb_agent TUI 主应用"""

    TITLE = "nb_agent"
    CSS_PATH = "styles.tcss"

    COMMANDS = App.COMMANDS | {AgentCommands}

    BINDINGS = [
        Binding("ctrl+j", "send_msg", "发送", show=True, priority=True),
        Binding("ctrl+k", "stop_ai", "终止", show=True, priority=True),
        Binding("ctrl+up", "edit_last", "编辑上轮", show=True, priority=True),
        Binding("tab", "select_model", "模型", show=True, priority=True),
        Binding("ctrl+n", "new_session", "新建", show=True, priority=True),
        Binding("ctrl+r", "resume_session", "恢复", show=True, priority=True),
        Binding("ctrl+e", "toggle_input", "展开", show=True, priority=True),
        Binding("ctrl+l", "clear_chat", "清屏", show=True),
        Binding("f1", "show_help", "帮助", show=True),
        Binding("f2", "show_skills", "Skills", show=True),
        Binding("f3", "toggle_tool_groups", "工具组", show=True),
        Binding("ctrl+q", "quit", "退出", show=True, priority=True),
    ]

    def __init__(self, config: dict):
        super().__init__()
        self.agent = AgentCore(config)
        self.config = config
        self._sending = False
        self._cancel_requested = False
        self._last_ai_reply = ""
        self._show_thinking = True
        self._spinner_idx = 0
        self._marquee_pos = 0
        self._spinner_timer = None
        self._send_start_time: float = 0.0
        self._last_elapsed: float = 0.0

        self.agent.approval_callback = self._request_tool_approval

    async def _request_tool_approval(self, tool_name: str, tool_args: dict) -> bool:
        future: asyncio.Future[bool] = asyncio.get_running_loop().create_future()

        def on_result(approved: Optional[bool]) -> None:
            if not future.done():
                future.set_result(bool(approved))

        self.push_screen(ToolApprovalScreen(tool_name, tool_args), on_result)
        return await future

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Horizontal(id="main-area"):
            yield RichLog(id="chat-panel", wrap=True, markup=True, highlight=True, auto_scroll=True)
            yield ToolPanel(self.agent, id="tool-panel")
        yield ChatInput(id="user-input")
        with Horizontal(id="ai-status-row"):
            yield Static("", id="ai-status-bar")
            yield Static("", id="ai-timer")
        yield Footer()

    async def on_mount(self):
        chat = self.query_one("#chat-panel", RichLog)
        model = self.agent.get_model_name()
        total = len(self.agent.available_models)
        chat.write(f"[bold #00d4aa]nb_agent[/bold #00d4aa] | 模型: [bold #4d96ff]{model}[/bold #4d96ff] | 共 [#ffd93d]{total}[/#ffd93d] 个可用模型")
        chat.write("[#6b7394]Enter=换行 | Ctrl+J=发送 | Tab=切换模型 | @=补全 | Ctrl+P=命令面板 | F1=帮助[/#6b7394]\n")
        self._update_subtitle()
        self.query_one("#user-input", ChatInput).focus()

        mcp_config = self.config.get("mcp", {})
        enabled_count = sum(1 for v in mcp_config.values() if v.get("enabled", True))
        if enabled_count > 0:
            chat.write(f"[#ff922b]⟳ {enabled_count} 个 MCP Server 后台连接中...[/#ff922b]")
            self.run_worker(self._connect_mcp_background(), exclusive=False)

    async def _connect_mcp_background(self):
        await self.agent.connect_mcp()
        chat = self.query_one("#chat-panel", RichLog)
        status = self.agent.get_mcp_status()
        ok = sum(1 for s in status if s["connected"])
        fail = len(status) - ok
        if ok > 0:
            chat.write(f"[#6bcb77]✓ {ok} 个 MCP Server 已连接[/#6bcb77]")
        if fail > 0:
            for s in status:
                if not s["connected"]:
                    chat.write(f"[#ff6b6b]✗ {s['name']}: {s['error']}[/#ff6b6b]")
        self.query_one("#tool-panel", ToolPanel).update_content()

    def _update_subtitle(self):
        title = self.agent.session_store.get_session_title(self.agent.session_id)
        if title and title != "新会话":
            self.sub_title = title
            self._set_terminal_title(f"nb_agent - {title}")
        else:
            self.sub_title = ""
            self._set_terminal_title("nb_agent")

    @staticmethod
    def _set_terminal_title(title: str):
        sys.stdout.write(f"\x1b]2;{title}\x07")
        sys.stdout.flush()

    # ─── 思考动画 ───────────────────────────────────────

    def _start_thinking_animation(self) -> None:
        self._spinner_idx = 0
        self._marquee_pos = 0
        if self._spinner_timer is not None:
            self._spinner_timer.stop()
        self._spinner_timer = self.set_interval(0.12, self._tick_spinner)

    def _stop_thinking_animation(self) -> None:
        if self._spinner_timer is not None:
            self._spinner_timer.stop()
            self._spinner_timer = None
        try:
            self.query_one("#ai-status-bar", Static).update("")
            self.query_one("#ai-timer", Static).update("")
        except Exception:
            pass

    def _tick_spinner(self) -> None:
        if not self._sending:
            self._stop_thinking_animation()
            return

        frame = _SPINNER_BIG[self._spinner_idx % len(_SPINNER_BIG)]
        base = f"  {frame}  AI is thinking...  Ctrl+K stop  *  "
        pos = self._marquee_pos % len(base)
        shifted = base[pos:] + base[:pos]
        full = (shifted * 6)[:120]

        marquee = Text()
        color_step = self._spinner_idx * 2
        for i, char in enumerate(full):
            color = _RAINBOW_COLORS[(i + color_step) % len(_RAINBOW_COLORS)]
            marquee.append(char, style=f"bold {color} on #0a0015")

        elapsed = time.monotonic() - self._send_start_time
        if elapsed < 60:
            time_val = f"{elapsed:.1f}s"
        elif elapsed < 3600:
            time_val = f"{int(elapsed // 60)}m{elapsed % 60:.0f}s"
        else:
            time_val = f"{int(elapsed // 3600)}h{int(elapsed % 3600 // 60)}m"

        spin_chars = _SPINNER_FRAMES
        spin = spin_chars[self._spinner_idx % len(spin_chars)]
        pulse = ["#ffd700", "#ff6b00", "#ff0080", "#a855f7", "#00d4ff", "#00ff88", "#ffd700"]
        tc = pulse[self._spinner_idx % len(pulse)]
        timer = Text()
        timer.append(f" {spin} ", style=f"bold {tc} on #0d0020")
        timer.append(f"{time_val} ", style=f"bold {tc} on #0d0020")

        self._spinner_idx += 1
        self._marquee_pos += 2
        try:
            self.query_one("#ai-status-bar", Static).update(marquee)
            self.query_one("#ai-timer", Static).update(timer)
        except Exception:
            pass

    # ─── 消息发送 ───────────────────────────────────────

    async def _do_send(self, user_text: str):
        chat = self.query_one("#chat-panel", RichLog)
        is_first_msg = len([m for m in self.agent.messages if m.get("role") == "user"]) == 0
        self._cancel_requested = False
        self._send_start_time = time.monotonic()
        self._start_thinking_animation()

        chat.write(Panel(
            Text(user_text, style="bold #f0f0f0 on #1a2744", overflow="fold"),
            border_style="bold #00d4ff",
            title="[bold #00d4ff]💎 user[/bold #00d4ff]",
            title_align="left",
            subtitle="[dim #00d4ff]━━━[/dim #00d4ff]",
            subtitle_align="right",
            padding=(0, 1),
        ))
        chat.write(f"[#7c3aed]({self.agent.get_model_name()}) 思考中...[/#7c3aed]")

        skill_context = self._extract_skill_mentions(user_text)
        if skill_context:
            self.agent.messages.append({"role": "system", "content": skill_context})

        try:
            use_stream = self.config.get("agent", {}).get("streaming", True)
            if use_stream:
                await self._handle_stream(user_text, chat)
            else:
                await self._handle_non_stream(user_text, chat)
        except Exception as e:
            chat.write(f"[#ff6b6b]发送失败: {type(e).__name__}: {e}[/#ff6b6b]")
        finally:
            self._stop_thinking_animation()
            self._sending = False
            try:
                self.query_one("#tool-panel", ToolPanel).update_content(last_elapsed=self._last_elapsed)
                self.query_one("#user-input", ChatInput).focus()
            except Exception:
                pass

        if is_first_msg:
            self._update_subtitle()
            self.run_worker(self._generate_title(), exclusive=False)

    async def _generate_title(self):
        try:
            await self.agent.generate_smart_title()
            self._update_subtitle()
        except Exception:
            pass

    def _is_at_bottom(self, chat: RichLog) -> bool:
        return chat.scroll_y >= chat.max_scroll_y - 2

    def _smart_scroll(self, chat: RichLog):
        if self._is_at_bottom(chat):
            chat.scroll_end(animate=False)

    async def _handle_stream(self, user_text: str, chat: RichLog):
        chat.auto_scroll = False
        model_label = self.agent.get_model_name()
        chat.write(f"[bold #4d96ff]🤖 {model_label}[/bold #4d96ff]")
        self._smart_scroll(chat)
        line_buffer = ""
        in_thinking = False
        full_reply_lines = []

        cancelled = False
        async for chunk in self.agent.chat_stream(user_text):
            if self._cancel_requested:
                cancelled = True
                break
            line_buffer += chunk
            await asyncio.sleep(0)

            if "<think>" in line_buffer and not in_thinking:
                in_thinking = True
                line_buffer = line_buffer.replace("<think>", "")
                if self._show_thinking:
                    chat.write("[italic #a78bfa]💭 思考过程:[/italic #a78bfa]")
                    self._smart_scroll(chat)

            if "</think>" in line_buffer and in_thinking:
                in_thinking = False
                before = line_buffer.split("</think>")[0]
                after = line_buffer.split("</think>", 1)[1]
                if self._show_thinking:
                    for line in before.split("\n"):
                        if line.strip():
                            chat.write(Text(line, style="#a78bfa"))
                    chat.write("[italic #7c3aed]── 思考结束 ──[/italic #7c3aed]")
                    self._smart_scroll(chat)
                line_buffer = after.lstrip("\n")
                continue

            while "\n" in line_buffer:
                line, line_buffer = line_buffer.split("\n", 1)
                if in_thinking and not self._show_thinking:
                    continue
                if not line.strip() and in_thinking:
                    continue
                if in_thinking:
                    chat.write(Text(line, style="#a78bfa"))
                elif line.strip():
                    chat.write(Text(line))
                    full_reply_lines.append(line)
                self._smart_scroll(chat)

        if cancelled:
            chat.write("[#ff6b6b]⏹ 已终止回答[/#ff6b6b]")
            self._cancel_requested = False
        else:
            if line_buffer:
                if in_thinking and self._show_thinking:
                    chat.write(Text(line_buffer, style="#a78bfa"))
                elif not in_thinking:
                    chat.write(Text(line_buffer))
                    full_reply_lines.append(line_buffer)

        self._last_ai_reply = "\n".join(full_reply_lines)

        if not cancelled:
            self._redraw_chat()
            chat = self.query_one("#chat-panel", RichLog)

        elapsed = time.monotonic() - self._send_start_time
        self._last_elapsed = elapsed
        t = self.agent.get_token_usage()
        tc_str = f" | 工具{t['last_tool_calls']}次" if t['last_tool_calls'] > 0 else ""
        chat.write(f"[#6b7394](本次 入{_fmt_tokens(t['last_prompt'])}+出{_fmt_tokens(t['last_completion'])}={_fmt_tokens(t['last_total'])} | 耗时{elapsed:.1f}s{tc_str} | 累计 {_fmt_tokens(t['total'])})[/#6b7394]")
        chat.auto_scroll = True
        chat.scroll_end(animate=False)

    async def _handle_non_stream(self, user_text: str, chat: RichLog):
        response = await self.agent.chat(user_text)

        for tc in response.tool_calls:
            chat.write(Panel(
                Text(tc.args, style="#fbbf24", overflow="fold"),
                border_style="#d97706",
                title=f"[bold #fbbf24]🔧 {tc.name}[/bold #fbbf24]",
                title_align="left",
                padding=(0, 1),
            ))
            result = tc.result[:5000] if len(tc.result) > 5000 else tc.result
            chat.write(Panel(
                Text(result, style="#86efac", overflow="fold"),
                border_style="#22c55e",
                title="[bold #86efac]📋 返回结果[/bold #86efac]",
                title_align="left",
                padding=(0, 1),
            ))

        if response.reasoning and self._show_thinking:
            chat.write(Panel(
                Text(response.reasoning, style="italic #a78bfa", overflow="fold"),
                border_style="#7c3aed",
                title="[bold #a78bfa]💭 思考过程[/bold #a78bfa]",
                title_align="left",
                padding=(0, 1),
            ))

        model_label = self.agent.get_model_name()
        chat.write(f"[bold #4d96ff]🤖 {model_label}[/bold #4d96ff]")
        chat.write(RichMarkdown(response.text))
        self._last_ai_reply = response.text
        elapsed = time.monotonic() - self._send_start_time
        self._last_elapsed = elapsed
        t = self.agent.get_token_usage()
        tc_str = f" | 工具{t['last_tool_calls']}次" if t['last_tool_calls'] > 0 else ""
        chat.write(f"[#6b7394](本次 入{_fmt_tokens(t['last_prompt'])}+出{_fmt_tokens(t['last_completion'])}={_fmt_tokens(t['last_total'])} | 耗时{elapsed:.1f}s{tc_str} | 累计 {_fmt_tokens(t['total'])})[/#6b7394]")

    # ─── 快捷键 Actions ────────────────────────────────

    def action_stop_ai(self):
        if isinstance(self.screen, ModalScreen):
            self.screen.dismiss()
            return
        if self._sending:
            self._cancel_requested = True
            self.notify("正在终止 AI 回答...", timeout=2)

    def action_edit_last(self):
        if self._sending:
            self.notify("请等待 AI 回答完成", severity="warning", timeout=2)
            return
        self._edit_last_message()

    async def action_send_msg(self):
        if self._sending:
            return
        input_widget = self.query_one("#user-input", ChatInput)
        user_text = input_widget.text.strip()
        if not user_text:
            return
        input_widget.clear()
        self._sending = True
        self.run_worker(self._do_send(user_text), exclusive=False)

    def action_new_session(self):
        if self._sending:
            self.notify("请等待 AI 回答完成", severity="warning", timeout=2)
            return
        self._cmd_new_session()

    def action_resume_session(self):
        self.push_screen(SessionSelectScreen(self.agent), self._on_session_selected)

    def action_show_help(self):
        self.push_screen(HelpScreen())

    def action_toggle_input(self):
        input_widget = self.query_one("#user-input", ChatInput)
        input_widget.toggle_class("expanded")
        input_widget.focus()

    def action_show_skills(self):
        self.push_screen(SkillListScreen(self.agent), self._on_skill_selected)

    def action_toggle_tool_groups(self):
        self.push_screen(ToolGroupToggleScreen(self.agent), self._on_tool_groups_closed)

    def _on_tool_groups_closed(self, _result=None):
        self.query_one("#tool-panel", ToolPanel).update_content()
        self.query_one("#user-input", ChatInput).focus()

    def on_chat_input_mention_triggered(self, event: ChatInput.MentionTriggered) -> None:
        candidates = self._build_mention_candidates()
        if candidates:
            self.push_screen(MentionSelectScreen(candidates), self._on_mention_selected)

    def _build_mention_candidates(self) -> list:
        candidates = []
        for t in self.agent.get_tools():
            if t["name"] == "view_skill" or t.get("disabled"):
                continue
            candidates.append({
                "name": t["name"],
                "func_name": t.get("func_name", t["name"]),
                "group": t.get("group", ""),
                "description": t["description"],
                "type": "tool",
                "source": t["source"],
            })
        for s in self.agent.skill_manager.get_all_skills():
            candidates.append({
                "name": s["name"],
                "description": s["description"],
                "type": "skill",
                "source": "Skill",
                "manual_only": s.get("manual_only", False),
            })
        return candidates

    def _on_mention_selected(self, prefixed_name: str) -> None:
        input_widget = self.query_one("#user-input", ChatInput)
        if prefixed_name:
            input_widget.insert(prefixed_name + " ")
        input_widget.focus()

    def action_clear_chat(self):
        if self._sending:
            self.notify("请等待 AI 回答完成", severity="warning", timeout=2)
            return
        chat = self.query_one("#chat-panel", RichLog)
        chat.clear()
        self.agent.clear_history()
        chat.write("[#6b7394]对话已清空，上下文已重置[/#6b7394]\n")

    def action_select_model(self):
        self.push_screen(ModelSelectScreen(self.agent), self._on_model_selected)

    async def on_unmount(self):
        await self.agent.disconnect_mcp()

    # ─── 命令面板回调 ──────────────────────────────────

    def _cmd_new_session(self):
        chat = self.query_one("#chat-panel", RichLog)
        self.agent.clear_history()
        chat.clear()
        chat.write("[#6b7394]✦ 新会话已创建，上下文已重置[/#6b7394]\n")
        self.query_one("#tool-panel", ToolPanel).update_content()
        self._update_subtitle()

    def _cmd_toggle_thinking(self):
        self._show_thinking = not self._show_thinking
        state = "显示" if self._show_thinking else "隐藏"
        self._redraw_chat()
        self.notify(f"思考过程已{state}", timeout=2)

    def _cmd_export_markdown(self):
        self.push_screen(RoundsInputScreen("导出 Markdown 文件"), self._on_export_rounds)

    def _cmd_copy_markdown(self):
        self.push_screen(RoundsInputScreen("复制为 Markdown"), self._on_copy_rounds)

    # ─── 弹窗回调 ──────────────────────────────────────

    def _on_model_selected(self, model_name):
        if not model_name:
            self.query_one("#user-input", ChatInput).focus()
            return
        old = self.agent.get_model_name()
        if self.agent.switch_model(model_name):
            new = self.agent.get_model_name()
            chat = self.query_one("#chat-panel", RichLog)
            chat.write(f"\n[bold #ffd93d]✦ 模型已切换:[/bold #ffd93d] [#6b7394]{old}[/#6b7394] → [bold #00d4aa]{new}[/bold #00d4aa]")
            self._update_subtitle()
            self.query_one("#tool-panel", ToolPanel).update_content()
        self.query_one("#user-input", ChatInput).focus()

    def _on_skill_selected(self, skill_name):
        if not skill_name:
            self.query_one("#user-input", ChatInput).focus()
            return
        skill_data = self.agent.skill_manager.view_skill(skill_name)
        if skill_data.get("success"):
            self.push_screen(SkillContentScreen(skill_data))
        else:
            self.notify(skill_data.get("error", "加载失败"), severity="warning", timeout=3)
        self.query_one("#user-input", ChatInput).focus()

    def _on_session_selected(self, session_id):
        if not session_id:
            self.query_one("#user-input", ChatInput).focus()
            return
        if session_id == self.agent.session_id:
            self.notify("已是当前会话", timeout=2)
            self.query_one("#user-input", ChatInput).focus()
            return
        sessions = self.agent.get_session_list(20)
        title = ""
        for s in sessions:
            if s["id"] == session_id:
                title = s["title"]
                break
        self.run_worker(self._cmd_resume_session(session_id, title), exclusive=False)
        self.query_one("#user-input", ChatInput).focus()

    async def _cmd_resume_session(self, session_id: str, title: str):
        chat = self.query_one("#chat-panel", RichLog)
        msgs = self.agent.session_store.get_messages(session_id)
        self.agent.session_id = session_id
        self.agent.messages = [{"role": "system", "content": self.agent.system_prompt}]
        for m in msgs:
            self.agent.messages.append({"role": m["role"], "content": m["content"]})
        chat.clear()
        chat.write(f"[#6bcb77]✦ 已恢复会话: {title}[/#6bcb77]")
        for m in msgs:
            if m["role"] == "user":
                chat.write(Panel(
                    Text(m["content"], style="bold #f0f0f0 on #1a2744", overflow="fold"),
                    border_style="bold #00d4ff",
                    title="[bold #00d4ff]💎 user[/bold #00d4ff]",
                    title_align="left",
                    subtitle="[dim #00d4ff]━━━[/dim #00d4ff]",
                    subtitle_align="right",
                    padding=(0, 1),
                ))
            elif m["role"] == "assistant" and m["content"]:
                chat.write("[bold #4d96ff]🤖 AI[/bold #4d96ff]")
                chat.write(RichMarkdown(m["content"]))
        self._update_subtitle()

    def _on_export_rounds(self, rounds):
        if rounds is None or rounds < 0:
            return
        self._export_markdown(rounds)

    def _on_copy_rounds(self, rounds):
        if rounds is None or rounds < 0:
            return
        self._copy_markdown(rounds)

    # ─── 编辑 / 导出 / 复制 ────────────────────────────

    def _edit_last_message(self):
        msgs = self.agent.messages
        last_user_idx = -1
        for i in range(len(msgs) - 1, -1, -1):
            if msgs[i].get("role") == "user":
                last_user_idx = i
                break
        if last_user_idx < 0:
            self.notify("没有可编辑的消息", severity="warning", timeout=2)
            return
        last_user_text = msgs[last_user_idx].get("content", "")
        self.agent.messages = msgs[:last_user_idx]
        input_widget = self.query_one("#user-input", ChatInput)
        input_widget.clear()
        input_widget.insert(last_user_text)
        input_widget.focus()
        self._redraw_chat()
        self.notify("已撤回上轮对话，可编辑后重新发送", timeout=3)

    def _show_tool_details(self):
        self.push_screen(ToolDetailScreen(self.agent))

    def _get_round_messages(self, rounds: int = 0) -> list:
        """获取最近 N 轮对话的消息列表，rounds=0 返回全部"""
        messages = self.agent.messages
        if rounds <= 0:
            return messages
        user_count = 0
        start_idx = 0
        for i in range(len(messages) - 1, -1, -1):
            if messages[i].get("role") == "user":
                user_count += 1
                if user_count == rounds:
                    start_idx = i
                    break
        if user_count < rounds:
            start_idx = 0
        result = [m for m in messages if m.get("role") == "system"]
        result.extend(m for i, m in enumerate(messages) if m.get("role") != "system" and i >= start_idx)
        return result

    def _export_markdown(self, rounds: int = 0):
        messages = self._get_round_messages(rounds)
        session_title = self.agent.session_store.get_session_title(self.agent.session_id) or ""
        display_title = session_title if session_title and session_title != "新会话" else f"会话 {self.agent.session_id[:8]}"
        lines = [f"# {display_title}\n"]
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "") or ""
            if role == "system":
                continue
            elif role == "user":
                lines.append(f"## 用户\n\n{content}\n")
            elif role == "assistant":
                reasoning = msg.get("reasoning_content", "")
                if reasoning:
                    lines.append(f"<details><summary>💭 思考过程</summary>\n\n{reasoning}\n\n</details>\n")
                tool_calls = msg.get("tool_calls", [])
                for tc in tool_calls:
                    func = tc.get("function", {})
                    name = func.get("name", "?")
                    args = func.get("arguments", "{}")
                    lines.append(f"### 🔧 调用工具: {name}\n\n```json\n{args}\n```\n")
                if content:
                    lines.append(f"## AI\n\n{content}\n")
            elif role == "tool":
                tool_name = msg.get("name", "tool")
                lines.append(f"> 📋 **{tool_name} 返回**: {content}\n")

        if len(lines) <= 1:
            self.notify("没有对话内容", severity="warning", timeout=2)
            return

        save_dir = os.path.join(Path.home(), ".nb_agent", "exports")
        os.makedirs(save_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if session_title and session_title != "新会话":
            safe_title = re.sub(r'[\\/:*?"<>|\s]+', '_', session_title)[:50].strip('_')
            filename = f"chat_{timestamp}_{safe_title}.md"
        else:
            filename = f"chat_{timestamp}_{self.agent.session_id[:8]}.md"
        filepath = os.path.join(save_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        self.notify(f"已导出: {filepath}", timeout=4)

    def _copy_markdown(self, rounds: int = 0):
        messages = self._get_round_messages(rounds)
        lines = []
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "") or ""
            if role == "system":
                continue
            elif role == "user":
                lines.append(f"## 用户\n\n{content}\n")
            elif role == "assistant":
                reasoning = msg.get("reasoning_content", "")
                if reasoning:
                    lines.append(f"<details><summary>💭 思考过程</summary>\n\n{reasoning}\n\n</details>\n")
                tool_calls = msg.get("tool_calls", [])
                for tc in tool_calls:
                    func = tc.get("function", {})
                    name = func.get("name", "?")
                    args = func.get("arguments", "{}")
                    lines.append(f"### 🔧 调用工具: {name}\n\n```json\n{args}\n```\n")
                if content:
                    lines.append(f"## AI\n\n{content}\n")
            elif role == "tool":
                tool_name = msg.get("name", "tool")
                lines.append(f"> 📋 **{tool_name} 返回**: {content}\n")

        if not lines:
            self.notify("没有对话内容", severity="warning", timeout=2)
            return
        self.copy_to_clipboard("\n".join(lines))
        rounds_hint = f"最近 {rounds} 轮" if rounds > 0 else "全部"
        self.notify(f"{rounds_hint}对话 Markdown 已复制到剪贴板", timeout=3)

    # ─── @ mention 预处理 ──────────────────────────────

    def _extract_skill_mentions(self, text: str) -> str:
        """从消息中提取 @skill:name 引用，加载 SKILL.md 内容作为临时系统指令。"""
        skill_mentions = re.findall(r'@skill:([\w-]+)', text)
        if not skill_mentions:
            return ""

        injected = []
        for name in skill_mentions:
            skill_data = self.agent.skill_manager.view_skill(name)
            if skill_data.get("success"):
                injected.append(
                    f"[Skill: {name}]\n"
                    f"以下是 Skill '{name}' 的指导文档，请据此完成任务：\n\n"
                    f"{skill_data['content']}"
                )
        return "\n\n---\n".join(injected) if injected else ""

    # ─── 聊天重绘 ──────────────────────────────────────

    def _redraw_chat(self):
        chat = self.query_one("#chat-panel", RichLog)
        chat.clear()
        total = len(self.agent.available_models)
        chat.write(f"[bold #00d4aa]nb_agent[/bold #00d4aa] | 共 [#ffd93d]{total}[/#ffd93d] 个可用模型")
        chat.write("[#6b7394]Enter=换行 | Ctrl+J=发送 | Ctrl+↑=编辑上条 | F1=帮助[/#6b7394]\n")

        last_assistant_idx = -1
        for i in range(len(self.agent.messages) - 1, -1, -1):
            if self.agent.messages[i].get("role") == "assistant" and self.agent.messages[i].get("reasoning_content"):
                last_assistant_idx = i
                break

        for idx, msg in enumerate(self.agent.messages):
            role = msg.get("role", "")
            content = msg.get("content", "") or ""
            if role == "system":
                continue
            elif role == "user":
                chat.write(Panel(
                    Text(content, style="bold #f0f0f0 on #1a2744", overflow="fold"),
                    border_style="bold #00d4ff",
                    title="[bold #00d4ff]💎 user[/bold #00d4ff]",
                    title_align="left",
                    subtitle="[dim #00d4ff]━━━[/dim #00d4ff]",
                    subtitle_align="right",
                    padding=(0, 1),
                ))
            elif role == "assistant":
                tool_calls = msg.get("tool_calls", [])
                reasoning = msg.get("reasoning_content", "")
                if tool_calls or content or reasoning:
                    model_label = msg.get("_model") or "AI"
                    chat.write(f"[bold #4d96ff]🤖 {model_label}[/bold #4d96ff]")
                if reasoning and self._show_thinking:
                    is_last = (idx == last_assistant_idx)
                    if is_last:
                        chat.write(Panel(
                            Text(reasoning, style="italic #a78bfa", overflow="fold"),
                            border_style="#7c3aed",
                            title="[bold #a78bfa]💭 思考过程[/bold #a78bfa]",
                            title_align="left",
                            padding=(0, 1),
                        ))
                    else:
                        char_count = len(reasoning)
                        chat.write(f"  [italic #7c3aed]💭 思考了 {char_count} 字 (Ctrl+P→切换思考显示 可查看全部)[/italic #7c3aed]")
                if tool_calls:
                    for tc in tool_calls:
                        func = tc.get("function", {})
                        name = func.get("name", "?")
                        args = func.get("arguments", "{}")
                        chat.write(Panel(
                            Text(args, style="#fbbf24", overflow="fold"),
                            border_style="#d97706",
                            title=f"[bold #fbbf24]🔧 {name}[/bold #fbbf24]",
                            title_align="left",
                            padding=(0, 1),
                        ))
                if content:
                    chat.write(RichMarkdown(content))
            elif role == "tool":
                result = content[:5000] if len(content) > 5000 else content
                tool_name = msg.get("name", "tool")
                chat.write(Panel(
                    Text(result, style="#86efac", overflow="fold"),
                    border_style="#22c55e",
                    title=f"[bold #86efac]📋 {tool_name} 返回[/bold #86efac]",
                    title_align="left",
                    padding=(0, 1),
                ))

`````

--- **end of file: nb_agent/tui/app.py** (project: nb_agent) --- 

---


--- **start of file: nb_agent/tui/styles.tcss** (project: nb_agent) --- 

`````text
/* nb_agent TUI — Modern Dark Theme */

Screen {
    background: #1a1b2e;
    layout: vertical;
}

Header {
    background: #0d0e1a;
    color: #00d4aa;
}

Footer {
    background: #0d0e1a;
    color: #6b7394;
}

Footer > .footer--key {
    background: #252742;
    color: #00d4aa;
}

/* ====== 主内容区 ====== */
#main-area {
    layout: horizontal;
    height: 1fr;
}

#chat-panel {
    width: 1fr;
    border: solid #2a2d4a;
    padding: 0 1;
    scrollbar-size-vertical: 1;
    scrollbar-color: #00d4aa;
    scrollbar-color-hover: #00ffc8;
    background: #12132a;
}

/* ====== 右侧信息面板 ====== */
#tool-panel {
    width: 38;
    border: solid #2a2d4a;
    padding: 0 1;
    background: #0f1025;
}

#section-tokens {
    height: auto;
    max-height: 5;
    padding: 0 0 1 0;
    color: #ffd93d;
}

#section-models-title {
    height: auto;
    max-height: 2;
    color: #4d96ff;
}

#section-models-list {
    height: 1fr;
    min-height: 5;
    border-bottom: solid #252742;
    scrollbar-size-vertical: 1;
    scrollbar-color: #4d96ff;
    background: #0f1025;
}

#section-models-list > .option-list--option-highlighted {
    background: #00897b;
    color: #e0f7fa;
}

#section-models-list > .option-list--option-hover {
    background: #1a3a4a;
}

#section-mcp-title {
    height: auto;
    max-height: 2;
    color: #ff922b;
    padding: 1 0 0 0;
}

#section-mcp-list {
    height: auto;
    max-height: 8;
    border-bottom: solid #252742;
    scrollbar-size-vertical: 1;
    scrollbar-color: #ff922b;
    background: #0f1025;
}

#section-mcp-list > .option-list--option-highlighted {
    background: #3a2a1a;
    color: #ffd93d;
}

#section-mcp-list > .option-list--option-hover {
    background: #2a1f14;
}

#section-tools-title {
    height: auto;
    max-height: 2;
    color: #6bcb77;
    padding: 1 0 0 0;
}

#section-tools-scroll {
    height: 1fr;
    min-height: 5;
    scrollbar-size-vertical: 1;
}

/* ====== 底部输入区 ====== */
#user-input {
    height: 4;
    margin: 0 1;
    border: round #3a3d5a;
    background: #12132a;
    color: #e0e0e0;
    scrollbar-size-vertical: 1;
    scrollbar-color: #00d4aa;
}

#user-input:focus {
    border: round #00d4aa;
}

#user-input.expanded {
    height: 14;
}

/* ====== 模型选择弹窗 ====== */
ModelSelectScreen {
    align: center middle;
    background: rgba(0, 0, 0, 0.7);
}

#model-dialog {
    width: 70;
    max-height: 80%;
    border: thick #00d4aa;
    background: #1a1b2e;
    padding: 1 2;
}

#model-title {
    text-align: center;
    width: 100%;
    height: 3;
    color: #00d4aa;
}

#model-list {
    height: 1fr;
    width: 100%;
    background: #12132a;
}

#model-list > .option-list--option-highlighted {
    background: #00897b;
    color: #e0f7fa;
}

/* ====== 会话选择弹窗 ====== */
SessionSelectScreen {
    align: center middle;
    background: rgba(0, 0, 0, 0.7);
}

#session-dialog {
    width: 70;
    max-height: 80%;
    border: thick #ff922b;
    background: #1a1b2e;
    padding: 1 2;
}

#session-title {
    text-align: center;
    width: 100%;
    height: 3;
    color: #ff922b;
}

#session-list {
    height: 1fr;
    width: 100%;
    background: #12132a;
}

#session-list > .option-list--option-highlighted {
    background: #00897b;
    color: #e0f7fa;
}

/* ====== 工具详情弹窗 ====== */
ToolDetailScreen {
    align: center middle;
    background: rgba(0, 0, 0, 0.7);
}

#tool-detail-dialog {
    width: 90%;
    max-width: 120;
    max-height: 80%;
    border: thick #6bcb77;
    background: #1a1b2e;
    padding: 1 2;
}

#tool-detail-content {
    width: 100%;
}

/* ====== 帮助弹窗 ====== */
HelpScreen {
    align: center middle;
    background: rgba(0, 0, 0, 0.7);
}

#help-dialog {
    width: 80%;
    max-width: 100;
    max-height: 80%;
    border: thick #4d96ff;
    background: #1a1b2e;
    padding: 1 2;
}

#help-content {
    width: 100%;
}

/* ====== 工具审批弹窗 ====== */
ToolApprovalScreen {
    align: center middle;
    background: rgba(0, 0, 0, 0.7);
}

#approval-dialog {
    width: 70%;
    max-width: 90;
    max-height: 60%;
    border: thick #ff6b6b;
    background: #1a1b2e;
    padding: 1 2;
}

#approval-title {
    text-align: center;
    width: 100%;
    height: 2;
}

#approval-tool {
    text-align: center;
    width: 100%;
    height: 2;
}

#approval-args-label {
    height: 1;
}

#approval-args-scroll {
    height: 1fr;
    min-height: 3;
    max-height: 15;
    border: solid #2a2d4a;
    background: #12132a;
    padding: 0 1;
    scrollbar-size-vertical: 1;
}

#approval-footer {
    text-align: center;
    height: 2;
    margin-top: 1;
}

/* ====== AI 回答跑马灯 + 计时器 ====== */
#ai-status-row {
    height: 1;
    width: 100%;
}

#ai-status-bar {
    width: 1fr;
    height: 1;
    background: #0a0015;
    text-align: left;
    overflow: hidden;
}

#ai-timer {
    width: auto;
    min-width: 10;
    height: 1;
    background: #1a0030;
    text-align: center;
    overflow: hidden;
}

/* ====== Skills 列表弹窗 ====== */
SkillListScreen {
    align: center middle;
    background: rgba(0, 0, 0, 0.7);
}

#skill-dialog {
    width: 80;
    max-height: 80%;
    border: thick #a78bfa;
    background: #1a1b2e;
    padding: 1 2;
}

#skill-title {
    text-align: center;
    width: 100%;
    height: 3;
    color: #a78bfa;
}

#skill-list {
    height: 1fr;
    width: 100%;
    background: #12132a;
}

#skill-list > .option-list--option-highlighted {
    background: #3a2a5a;
    color: #e0d4ff;
}

#skill-list > .option-list--option-hover {
    background: #2a1f3a;
}

/* ====== 工具分组切换弹窗 ====== */
ToolGroupToggleScreen {
    align: center middle;
    background: rgba(0, 0, 0, 0.7);
}

#group-toggle-dialog {
    width: 70;
    max-height: 60%;
    border: thick #6bcb77;
    background: #1a1b2e;
    padding: 1 2;
}

#group-toggle-title {
    text-align: center;
    width: 100%;
    height: 2;
    color: #6bcb77;
}

#group-toggle-list {
    height: 1fr;
    width: 100%;
    background: #12132a;
}

#group-toggle-list > .option-list--option-highlighted {
    background: #1a3a2a;
    color: #6bcb77;
}

/* ====== @ 补全弹窗 ====== */
MentionSelectScreen {
    align: center middle;
    background: rgba(0, 0, 0, 0.7);
}

#mention-dialog {
    width: 80;
    max-height: 70%;
    border: thick #ffd93d;
    background: #1a1b2e;
    padding: 1 2;
}

#mention-title {
    text-align: center;
    width: 100%;
    height: 2;
    color: #ffd93d;
}

#mention-filter {
    margin-bottom: 1;
}

#mention-list {
    height: 1fr;
    width: 100%;
    background: #12132a;
}

#mention-list > .option-list--option-highlighted {
    background: #3a3520;
    color: #ffd93d;
}

#mention-list > .option-list--option-hover {
    background: #2a2515;
}

/* ====== Skill 内容弹窗 ====== */
SkillContentScreen {
    align: center middle;
    background: rgba(0, 0, 0, 0.7);
}

#skill-content-dialog {
    width: 90%;
    max-width: 120;
    max-height: 85%;
    border: thick #a78bfa;
    background: #1a1b2e;
    padding: 1 2;
}

#skill-content-text {
    width: 100%;
}

/* ====== 轮次输入弹窗 ====== */
RoundsInputScreen {
    align: center middle;
    background: rgba(0, 0, 0, 0.7);
}

#rounds-dialog {
    width: 60%;
    max-width: 60;
    max-height: 30%;
    border: thick #ffd93d;
    background: #1a1b2e;
    padding: 1 2;
}

#rounds-title {
    text-align: center;
    margin-bottom: 1;
}

#rounds-hint {
    text-align: center;
    margin-bottom: 1;
}

#rounds-input {
    margin-bottom: 1;
}

#rounds-footer {
    text-align: center;
}

`````

--- **end of file: nb_agent/tui/styles.tcss** (project: nb_agent) --- 

---


--- **start of file: nb_agent/tui/__init__.py** (project: nb_agent) --- 


### 📄 Python File Metadata: `nb_agent/tui/__init__.py`


---

`````python

`````

--- **end of file: nb_agent/tui/__init__.py** (project: nb_agent) --- 

---


--- **start of file: nb_agent/tui/widgets/commands.py** (project: nb_agent) --- 


### 📄 Python File Metadata: `nb_agent/tui/widgets/commands.py`

#### 📝 Module Docstring

`````
TUI 命令面板 Provider
`````

#### 📦 Imports

- `from textual.command import Hit`
- `from textual.command import Hits`
- `from textual.command import Provider`
- `from textual.command import DiscoveryHit`

#### 🏛️ Classes (1)

##### 📌 `class AgentCommands(Provider)`
*Line: 6*

**Docstring:**
`````
命令面板: 提供会话管理、导出、设置等操作
`````

**Public Methods (2):**
- `async def discover(self) -> Hits`
- `async def search(self, query: str) -> Hits`


---

`````python
"""TUI 命令面板 Provider"""

from textual.command import Hit, Hits, Provider, DiscoveryHit


class AgentCommands(Provider):
    """命令面板: 提供会话管理、导出、设置等操作"""

    async def discover(self) -> Hits:
        app = self.app
        commands = [
            ("编辑上轮提问", "撤回最后一轮对话，重新编辑", app._edit_last_message),
            ("切换思考显示", "显示或隐藏 AI 的思考过程", app._cmd_toggle_thinking),
            ("查看工具详情", "查看所有工具的完整描述", app._show_tool_details),
            ("复制为 Markdown", "复制对话为 Markdown 到剪贴板", app._cmd_copy_markdown),
            ("导出 Markdown 文件", "将对话导出为 .md 文件", app._cmd_export_markdown),
        ]
        for name, help_text, callback in commands:
            yield DiscoveryHit(name, callback, help=help_text)

    async def search(self, query: str) -> Hits:
        matcher = self.matcher(query)
        app = self.app
        commands = [
            ("编辑上轮提问", "撤回最后一轮，重新编辑", app._edit_last_message),
            ("切换思考显示", "显示或隐藏思考过程", app._cmd_toggle_thinking),
            ("查看工具详情", "查看所有工具的完整描述", app._show_tool_details),
            ("复制为 Markdown", "复制对话为 Markdown 到剪贴板", app._cmd_copy_markdown),
            ("导出 Markdown 文件", "导出为 .md 文件", app._cmd_export_markdown),
        ]
        for name, help_text, callback in commands:
            score = matcher.match(name)
            if score > 0:
                yield Hit(score, matcher.highlight(name), callback, help=help_text)

`````

--- **end of file: nb_agent/tui/widgets/commands.py** (project: nb_agent) --- 

---


--- **start of file: nb_agent/tui/widgets/inputs.py** (project: nb_agent) --- 


### 📄 Python File Metadata: `nb_agent/tui/widgets/inputs.py`

#### 📝 Module Docstring

`````
聊天输入组件
`````

#### 📦 Imports

- `from textual import events`
- `from textual.message import Message`
- `from textual.widgets import Static`
- `from textual.widgets import TextArea`

#### 🏛️ Classes (2)

##### 📌 `class ChatInput(TextArea)`
*Line: 8*

**Docstring:**
`````
聊天输入框：Enter=换行，Ctrl+J=发送，@=触发补全
`````

**🔧 Constructor (`__init__`):**
- `def __init__(self, **kwargs)`
  - **Parameters:**
    - `self`
    - `**kwargs`

**Public Methods (1):**
- `def on_key(self, event: events.Key) -> None`

##### 📌 `class ClickableStatic(Static)`
*Line: 26*

**Docstring:**
`````
可点击的 Static 组件 — 点击时打开工具详情
`````

**Public Methods (1):**
- `def on_click(self, event)`


---

`````python
"""聊天输入组件"""

from textual import events
from textual.message import Message
from textual.widgets import Static, TextArea


class ChatInput(TextArea):
    """聊天输入框：Enter=换行，Ctrl+J=发送，@=触发补全"""

    class MentionTriggered(Message):
        """输入 @ 时触发，通知 App 打开补全弹窗"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.show_line_numbers = False

    def on_key(self, event: events.Key) -> None:
        if event.character == "@":
            self.set_timer(0.05, self._emit_mention)

    def _emit_mention(self) -> None:
        self.post_message(self.MentionTriggered())


class ClickableStatic(Static):
    """可点击的 Static 组件 — 点击时打开工具详情"""

    def on_click(self, event):
        app = self.app
        if hasattr(app, '_show_tool_details'):
            app._show_tool_details()

`````

--- **end of file: nb_agent/tui/widgets/inputs.py** (project: nb_agent) --- 

---


--- **start of file: nb_agent/tui/widgets/screens.py** (project: nb_agent) --- 


### 📄 Python File Metadata: `nb_agent/tui/widgets/screens.py`

#### 📝 Module Docstring

`````
TUI 弹窗：模型选择、帮助、会话恢复、工具详情、轮次输入、工具审批
`````

#### 📦 Imports

- `import json`
- `from typing import Optional`
- `from textual.app import ComposeResult`
- `from textual.containers import Vertical`
- `from textual.containers import VerticalScroll`
- `from textual.widgets import Input`
- `from textual.widgets import OptionList`
- `from textual.widgets import Static`
- `from textual.widgets.option_list import Option`
- `from textual.binding import Binding`
- `from textual.screen import ModalScreen`
- `from rich.text import Text`
- `from nb_agent.core import AgentCore`

#### 🏛️ Classes (10)

##### 📌 `class ModelSelectScreen(ModalScreen[str])`
*Line: 17*

**Docstring:**
`````
模型选择弹窗
`````

**🔧 Constructor (`__init__`):**
- `def __init__(self, agent: AgentCore, **kwargs)`
  - **Parameters:**
    - `self`
    - `agent: AgentCore`
    - `**kwargs`

**Public Methods (4):**
- `def compose(self) -> ComposeResult`
- `def on_mount(self)`
- `def on_option_list_option_selected(self, event: OptionList.OptionSelected)`
- `def action_dismiss_modal(self)`

**Class Variables (1):**
- `BINDINGS = [Binding('escape', 'dismiss_modal', '返回')]`

##### 📌 `class HelpScreen(ModalScreen)`
*Line: 59*

**Docstring:**
`````
帮助弹窗
`````

**Public Methods (2):**
- `def compose(self) -> ComposeResult`
- `def action_dismiss_modal(self)`

**Class Variables (1):**
- `BINDINGS = [Binding('escape', 'dismiss_modal', '返回'), Binding('f1', 'dismiss_modal', '返回'), Binding('enter', 'dismiss_modal', '返回')]`

##### 📌 `class SessionSelectScreen(ModalScreen[str])`
*Line: 125*

**Docstring:**
`````
会话选择弹窗
`````

**🔧 Constructor (`__init__`):**
- `def __init__(self, agent: AgentCore, **kwargs)`
  - **Parameters:**
    - `self`
    - `agent: AgentCore`
    - `**kwargs`

**Public Methods (4):**
- `def compose(self) -> ComposeResult`
- `def on_mount(self)`
- `def on_option_list_option_selected(self, event: OptionList.OptionSelected)`
- `def action_dismiss_modal(self)`

**Class Variables (1):**
- `BINDINGS = [Binding('escape', 'dismiss_modal', '返回')]`

##### 📌 `class ToolDetailScreen(ModalScreen)`
*Line: 175*

**Docstring:**
`````
工具详情弹窗
`````

**🔧 Constructor (`__init__`):**
- `def __init__(self, agent: AgentCore, **kwargs)`
  - **Parameters:**
    - `self`
    - `agent: AgentCore`
    - `**kwargs`

**Public Methods (2):**
- `def compose(self) -> ComposeResult`
- `def action_dismiss_modal(self)`

**Class Variables (1):**
- `BINDINGS = [Binding('escape', 'dismiss_modal', '返回'), Binding('enter', 'dismiss_modal', '返回')]`

##### 📌 `class RoundsInputScreen(ModalScreen[int])`
*Line: 212*

**Docstring:**
`````
轮次输入弹窗：用户输入要导出/复制的对话轮次，0=全部
`````

**🔧 Constructor (`__init__`):**
- `def __init__(self, action_name: str, **kwargs)`
  - **Parameters:**
    - `self`
    - `action_name: str`
    - `**kwargs`

**Public Methods (5):**
- `def compose(self) -> ComposeResult`
- `def on_mount(self)`
- `def on_input_submitted(self, event: Input.Submitted)`
- `def action_confirm(self)`
- `def action_cancel(self)`

**Class Variables (1):**
- `BINDINGS = [Binding('escape', 'cancel', '取消')]`

##### 📌 `class SkillListScreen(ModalScreen[str])`
*Line: 253*

**Docstring:**
`````
Skills 列表弹窗
`````

**🔧 Constructor (`__init__`):**
- `def __init__(self, agent: AgentCore, **kwargs)`
  - **Parameters:**
    - `self`
    - `agent: AgentCore`
    - `**kwargs`

**Public Methods (4):**
- `def compose(self) -> ComposeResult`
- `def on_mount(self)`
- `def on_option_list_option_selected(self, event: OptionList.OptionSelected)`
- `def action_dismiss_modal(self)`

**Class Variables (1):**
- `BINDINGS = [Binding('escape', 'dismiss_modal', '返回')]`

##### 📌 `class SkillContentScreen(ModalScreen)`
*Line: 299*

**Docstring:**
`````
Skill 内容详情弹窗
`````

**🔧 Constructor (`__init__`):**
- `def __init__(self, skill_data: dict, **kwargs)`
  - **Parameters:**
    - `self`
    - `skill_data: dict`
    - `**kwargs`

**Public Methods (2):**
- `def compose(self) -> ComposeResult`
- `def action_dismiss_modal(self)`

**Class Variables (1):**
- `BINDINGS = [Binding('escape', 'dismiss_modal', '返回'), Binding('enter', 'dismiss_modal', '返回')]`

##### 📌 `class MentionSelectScreen(ModalScreen[str])`
*Line: 340*

**Docstring:**
`````
@ 补全弹窗：搜索并选择工具或 Skill
`````

**🔧 Constructor (`__init__`):**
- `def __init__(self, candidates: list, **kwargs)`
  - **Parameters:**
    - `self`
    - `candidates: list`
    - `**kwargs`

**Public Methods (5):**
- `def compose(self) -> ComposeResult`
- `def on_mount(self)`
- `def on_input_changed(self, event: Input.Changed)`
- `def on_option_list_option_selected(self, event: OptionList.OptionSelected)`
- `def action_dismiss_modal(self)`

**Class Variables (1):**
- `BINDINGS = [Binding('escape', 'dismiss_modal', '返回')]`

##### 📌 `class ToolGroupToggleScreen(ModalScreen)`
*Line: 428*

**Docstring:**
`````
工具分组切换弹窗：点击分组启用/禁用
`````

**🔧 Constructor (`__init__`):**
- `def __init__(self, agent: AgentCore, **kwargs)`
  - **Parameters:**
    - `self`
    - `agent: AgentCore`
    - `**kwargs`

**Public Methods (4):**
- `def compose(self) -> ComposeResult`
- `def on_mount(self)`
- `def on_option_list_option_selected(self, event: OptionList.OptionSelected)`
- `def action_dismiss_modal(self)`

**Class Variables (1):**
- `BINDINGS = [Binding('escape', 'dismiss_modal', '返回')]`

##### 📌 `class ToolApprovalScreen(ModalScreen[bool])`
*Line: 492*

**Docstring:**
`````
工具审批弹窗：危险操作需要用户确认后才执行
`````

**🔧 Constructor (`__init__`):**
- `def __init__(self, tool_name: str, tool_args: dict, **kwargs)`
  - **Parameters:**
    - `self`
    - `tool_name: str`
    - `tool_args: dict`
    - `**kwargs`

**Public Methods (3):**
- `def compose(self) -> ComposeResult`
- `def action_approve(self)`
- `def action_reject(self)`

**Class Variables (1):**
- `BINDINGS = [Binding('enter', 'approve', '确认执行', priority=True), Binding('escape', 'reject', '拒绝', priority=True)]`


---

`````python
"""TUI 弹窗：模型选择、帮助、会话恢复、工具详情、轮次输入、工具审批"""

import json
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Input, OptionList, Static
from textual.widgets.option_list import Option
from textual.binding import Binding
from textual.screen import ModalScreen
from rich.text import Text

from nb_agent.core import AgentCore


class ModelSelectScreen(ModalScreen[str]):
    """模型选择弹窗"""

    BINDINGS = [
        Binding("escape", "dismiss_modal", "返回"),
    ]

    def __init__(self, agent: AgentCore, **kwargs):
        super().__init__(**kwargs)
        self.agent = agent

    def compose(self) -> ComposeResult:
        with Vertical(id="model-dialog"):
            yield Static("[bold]选择模型[/bold]  (↑↓选择, Enter确认, Esc返回)\n", id="model-title")
            yield OptionList(id="model-list")

    def on_mount(self):
        option_list = self.query_one("#model-list", OptionList)
        grouped = self.agent.get_models_grouped()
        current = self.agent.get_model_name()

        for provider_name, models in grouped.items():
            option_list.add_option(Option(
                Text(f"── {provider_name} ──", style="dim #6b7394"), disabled=True
            ))
            for m in models:
                if m.id == current:
                    label = Text(f"  ▶ {m.id} ({m.name})", style="bold #00d4aa")
                else:
                    label = Text(f"    {m.id} ({m.name})", style="#c0c0c0")
                option_list.add_option(Option(label, id=m.id))

        option_list.focus()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected):
        if event.option.id:
            self.dismiss(event.option.id)

    def action_dismiss_modal(self):
        self.dismiss("")


class HelpScreen(ModalScreen):
    """帮助弹窗"""

    BINDINGS = [
        Binding("escape", "dismiss_modal", "返回"),
        Binding("f1", "dismiss_modal", "返回"),
        Binding("enter", "dismiss_modal", "返回"),
    ]

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="help-dialog"):
            yield Static(self._build_help(), id="help-content")

    def _build_help(self) -> str:
        lines = []
        lines.append("[bold #00d4aa]═══ nb_agent 帮助 ═══[/bold #00d4aa]\n")

        lines.append("[bold #ffd93d]⌨ 快捷键[/bold #ffd93d]")
        keys = [
            ("Ctrl+J", "发送消息"),
            ("Enter", "输入框内换行"),
            ("Tab", "打开模型选择弹窗"),
            ("Ctrl+N", "新建会话"),
            ("Ctrl+K", "终止当前 AI 回答"),
            ("Ctrl+↑", "编辑上一轮提问"),
            ("Ctrl+R", "恢复历史会话"),
            ("Ctrl+E", "展开/收起输入框"),
            ("Ctrl+L", "清空屏幕"),
            ("Ctrl+P", "打开命令面板"),
            ("F1", "显示此帮助"),
            ("F2", "查看 Skills 列表"),
            ("F3", "工具分组管理（启用/禁用）"),
            ("Ctrl+Q", "退出程序"),
        ]
        for key, desc in keys:
            lines.append(f"  [#ffd93d]{key:<20}[/#ffd93d] [#c0c0c0]{desc}[/#c0c0c0]")

        lines.append("")
        lines.append("[bold #4d96ff]📋 命令面板 (Ctrl+P)[/bold #4d96ff]")
        cmds = [
            ("编辑上轮提问", "撤回最后一轮，重新编辑"),
            ("切换思考显示", "显示或隐藏 AI 思考过程"),
            ("查看工具详情", "查看所有工具完整描述"),
            ("复制完整对话", "复制 Markdown 到剪贴板"),
            ("复制最后回复", "复制到剪贴板"),
            ("导出/保存", "导出 .md 或保存 .txt"),
        ]
        for name, desc in cmds:
            lines.append(f"  [#4d96ff]{name:<18}[/#4d96ff] [#c0c0c0]{desc}[/#c0c0c0]")

        lines.append("")
        lines.append("[bold #6bcb77]💡 提示[/bold #6bcb77]")
        lines.append("  [#c0c0c0]• 输入 @ 自动弹出工具/Skill 补全[/#c0c0c0]")
        lines.append("  [#c0c0c0]• @skill:name 注入 Skill 指南，@tool:name 提示 AI 用该工具[/#c0c0c0]")
        lines.append("  [#c0c0c0]• 右侧面板可直接点击模型名称切换[/#c0c0c0]")
        lines.append("  [#c0c0c0]• MCP 工具在后台自动连接[/#c0c0c0]")
        lines.append("  [#c0c0c0]• 对话超长时自动截断早期消息[/#c0c0c0]")
        lines.append("  [#c0c0c0]• Alt+Shift+鼠标拖选 = 矩形区域选择[/#c0c0c0]")

        lines.append("\n[dim #6b7394]按 Esc / Enter / F1 关闭[/dim #6b7394]")
        return "\n".join(lines)

    def action_dismiss_modal(self):
        self.dismiss()


class SessionSelectScreen(ModalScreen[str]):
    """会话选择弹窗"""

    BINDINGS = [
        Binding("escape", "dismiss_modal", "返回"),
    ]

    def __init__(self, agent: AgentCore, **kwargs):
        super().__init__(**kwargs)
        self.agent = agent
        self._session_ids = []

    def compose(self) -> ComposeResult:
        with Vertical(id="session-dialog"):
            yield Static("[bold]恢复会话[/bold]  (↑↓选择, Enter确认, Esc返回)\n", id="session-title")
            yield OptionList(id="session-list")

    def on_mount(self):
        option_list = self.query_one("#session-list", OptionList)
        sessions = self.agent.get_session_list(20)
        current_id = self.agent.session_id

        if not sessions:
            option_list.add_option(Option(
                Text("没有历史会话", style="dim #6b7394"), disabled=True
            ))
            return

        for s in sessions:
            title = s["title"]
            date = s["updated_at"][:16]
            sid = s["id"]
            self._session_ids.append(sid)

            if sid == current_id:
                label = Text(f"  ▶ {title}  ({date})", style="bold #00d4aa")
            else:
                label = Text(f"    {title}  ({date})", style="#c0c0c0")
            option_list.add_option(Option(label, id=sid))

        option_list.focus()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected):
        if event.option.id:
            self.dismiss(event.option.id)

    def action_dismiss_modal(self):
        self.dismiss("")


class ToolDetailScreen(ModalScreen):
    """工具详情弹窗"""

    BINDINGS = [
        Binding("escape", "dismiss_modal", "返回"),
        Binding("enter", "dismiss_modal", "返回"),
    ]

    def __init__(self, agent: AgentCore, **kwargs):
        super().__init__(**kwargs)
        self.agent = agent

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="tool-detail-dialog"):
            yield Static(self._build_content(), id="tool-detail-content")

    def _build_content(self) -> str:
        tools = self.agent.get_tools()
        lines = [f"[bold #6bcb77]工具详情 ({len(tools)})[/bold #6bcb77]\n"]
        for t in tools:
            source = t.get("source", "")
            if source.startswith("MCP:"):
                icon = "[#b39ddb]◆[/#b39ddb]"
                src_label = f"[#b39ddb]{source}[/#b39ddb]"
            else:
                icon = "[#6bcb77]●[/#6bcb77]"
                src_label = f"[#6bcb77]{source}[/#6bcb77]"
            lines.append(f"{icon} [bold #c0c0c0]{t['name']}[/bold #c0c0c0]  {src_label}")
            lines.append(f"  [#8890a8]{t['description']}[/#8890a8]")
            lines.append("")
        lines.append("[dim #6b7394]按 Esc / Enter 关闭[/dim #6b7394]")
        return "\n".join(lines)

    def action_dismiss_modal(self):
        self.dismiss()


class RoundsInputScreen(ModalScreen[int]):
    """轮次输入弹窗：用户输入要导出/复制的对话轮次，0=全部"""

    BINDINGS = [
        Binding("escape", "cancel", "取消"),
    ]

    def __init__(self, action_name: str, **kwargs):
        super().__init__(**kwargs)
        self.action_name = action_name

    def compose(self) -> ComposeResult:
        with Vertical(id="rounds-dialog"):
            yield Static(f"[bold #ffd93d]{self.action_name}[/bold #ffd93d]", id="rounds-title")
            yield Static("[#c0c0c0]导出/复制最近 N 轮对话 (0 = 全部)[/#c0c0c0]", id="rounds-hint")
            yield Input(value="0", id="rounds-input")
            yield Static("[dim #6b7394]Enter 确认 | Esc 取消[/dim #6b7394]", id="rounds-footer")

    def on_mount(self):
        self.query_one("#rounds-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted):
        self._do_confirm(event.value)

    def action_confirm(self):
        text = self.query_one("#rounds-input", Input).value.strip()
        self._do_confirm(text)

    def _do_confirm(self, text: str):
        try:
            n = int(text.strip())
            if n < 0:
                n = 0
        except ValueError:
            n = 0
        self.dismiss(n)

    def action_cancel(self):
        self.dismiss(-1)


class SkillListScreen(ModalScreen[str]):
    """Skills 列表弹窗"""

    BINDINGS = [
        Binding("escape", "dismiss_modal", "返回"),
    ]

    def __init__(self, agent: AgentCore, **kwargs):
        super().__init__(**kwargs)
        self.agent = agent

    def compose(self) -> ComposeResult:
        with Vertical(id="skill-dialog"):
            yield Static("[bold]Skills 列表[/bold]  (↑↓选择, Enter 查看详情, Esc 返回)\n", id="skill-title")
            yield OptionList(id="skill-list")

    def on_mount(self):
        option_list = self.query_one("#skill-list", OptionList)
        all_skills = self.agent.skill_manager.get_all_skills()

        if not all_skills:
            option_list.add_option(Option(
                Text("没有发现 Skills", style="dim #6b7394"), disabled=True
            ))
            return

        for s in all_skills:
            name = s["name"]
            desc = s["description"]
            if len(desc) > 60:
                desc = desc[:60] + "..."
            manual = "  [仅手动]" if s.get("manual_only") else ""
            icon = "○" if s.get("manual_only") else "●"
            label = Text(f"  {icon} {name}{manual}  — {desc}", style="#c0c0c0")
            option_list.add_option(Option(label, id=name))

        option_list.focus()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected):
        if event.option.id:
            self.dismiss(event.option.id)

    def action_dismiss_modal(self):
        self.dismiss("")


class SkillContentScreen(ModalScreen):
    """Skill 内容详情弹窗"""

    BINDINGS = [
        Binding("escape", "dismiss_modal", "返回"),
        Binding("enter", "dismiss_modal", "返回"),
    ]

    def __init__(self, skill_data: dict, **kwargs):
        super().__init__(**kwargs)
        self.skill_data = skill_data

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="skill-content-dialog"):
            yield Static(self._build_content(), id="skill-content-text")

    def _build_content(self) -> str:
        d = self.skill_data
        lines = []
        lines.append(f"[bold #a78bfa]═══ Skill: {d.get('name', '?')} ═══[/bold #a78bfa]\n")
        lines.append(f"  [#ffd93d]来源:[/#ffd93d] {d.get('source', '?')}")
        lines.append(f"  [#ffd93d]路径:[/#ffd93d] {d.get('skill_path', '?')}")

        paths = d.get("paths", [])
        if paths:
            lines.append(f"  [#ffd93d]匹配:[/#ffd93d] {', '.join(paths)}")

        lines.append("")
        lines.append("[bold #4d96ff]── 内容 ──[/bold #4d96ff]\n")
        content = d.get("content", "无内容")
        for line in content.split("\n"):
            safe = line.replace("[", "\\[")
            lines.append(f"[#c0c0c0]{safe}[/#c0c0c0]")

        lines.append("\n[dim #6b7394]按 Esc / Enter 关闭[/dim #6b7394]")
        return "\n".join(lines)

    def action_dismiss_modal(self):
        self.dismiss()


class MentionSelectScreen(ModalScreen[str]):
    """@ 补全弹窗：搜索并选择工具或 Skill"""

    BINDINGS = [
        Binding("escape", "dismiss_modal", "返回"),
    ]

    def __init__(self, candidates: list, **kwargs):
        super().__init__(**kwargs)
        self.candidates = candidates

    def compose(self) -> ComposeResult:
        with Vertical(id="mention-dialog"):
            yield Static("[bold]@ 引用工具或 Skill[/bold]  (输入过滤, Enter 选择, Esc 返回)", id="mention-title")
            yield Input(placeholder="搜索...", id="mention-filter")
            yield OptionList(id="mention-list")

    def on_mount(self):
        self._render_list("")
        self.query_one("#mention-filter", Input).focus()

    def on_input_changed(self, event: Input.Changed):
        if event.input.id == "mention-filter":
            self._render_list(event.value)

    def _render_list(self, query: str):
        option_list = self.query_one("#mention-list", OptionList)
        option_list.clear_options()
        q = query.lower()

        tools = [c for c in self.candidates if c.get("type") != "skill"]
        skills = [c for c in self.candidates if c.get("type") == "skill"]

        filtered_tools = [c for c in tools if not q or q in c["name"].lower() or q in c.get("description", "").lower()]
        filtered_skills = [c for c in skills if not q or q in c["name"].lower() or q in c.get("description", "").lower()]

        if filtered_tools:
            last_group = None
            for c in filtered_tools:
                group = c.get("group", "")
                if group != last_group:
                    src = c.get("source", "")
                    if src.startswith("MCP:"):
                        option_list.add_option(Option(Text(f"── {group} ──", style="dim #b39ddb"), disabled=True))
                    elif group:
                        option_list.add_option(Option(Text(f"── {group} ──", style="dim #6bcb77"), disabled=True))
                    else:
                        option_list.add_option(Option(Text("── 工具 ──", style="dim #6bcb77"), disabled=True))
                    last_group = group

                name = c["name"]
                func_name = c.get("func_name", name)
                desc = c.get("description", "")
                if len(desc) > 50:
                    desc = desc[:50] + "..."
                source = c.get("source", "")

                if source.startswith("MCP:"):
                    icon, style = "◆", "#b39ddb"
                else:
                    icon, style = "●", "#6bcb77"

                label = Text(f"  {icon} {func_name}  ", style=f"bold {style}")
                label.append(desc, style="#8890a8")
                option_list.add_option(Option(label, id=f"tool:{name}"))

        if filtered_skills:
            if filtered_tools:
                option_list.add_option(Option(Text("", style="dim"), disabled=True))
            option_list.add_option(Option(Text("── Skills ──", style="dim #a78bfa"), disabled=True))
            for c in filtered_skills:
                name = c["name"]
                desc = c.get("description", "")
                if len(desc) > 50:
                    desc = desc[:50] + "..."
                manual = " [仅手动]" if c.get("manual_only") else ""
                label = Text(f"  ★ {name}{manual}  ", style="bold #a78bfa")
                label.append(desc, style="#8890a8")
                option_list.add_option(Option(label, id=f"skill:{name}"))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected):
        if event.option.id:
            self.dismiss(event.option.id)

    def action_dismiss_modal(self):
        self.dismiss("")


class ToolGroupToggleScreen(ModalScreen):
    """工具分组切换弹窗：点击分组启用/禁用"""

    BINDINGS = [
        Binding("escape", "dismiss_modal", "返回"),
    ]

    def __init__(self, agent: AgentCore, **kwargs):
        super().__init__(**kwargs)
        self.agent = agent

    def compose(self) -> ComposeResult:
        with Vertical(id="group-toggle-dialog"):
            yield Static("[bold]工具分组管理[/bold]  (Enter 切换启用/禁用, Esc 返回)", id="group-toggle-title")
            yield OptionList(id="group-toggle-list")

    def on_mount(self):
        self._render_groups()
        self.query_one("#group-toggle-list", OptionList).focus()

    def _render_groups(self):
        option_list = self.query_one("#group-toggle-list", OptionList)
        option_list.clear_options()
        groups = self.agent.get_tool_groups()

        if not groups:
            option_list.add_option(Option(Text("无工具分组", style="dim #6b7394"), disabled=True))
            return

        for g in groups:
            name = g["name"]
            count = g["count"]
            disabled = g["disabled"]
            source = g["source"]

            if name == "(无分组)":
                label = Text(f"  ● {name} ({count} 工具)", style="#6b7394")
                option_list.add_option(Option(label, disabled=True))
                continue

            if disabled:
                icon = "○"
                state = "[已禁用]"
                style = "#8890a8"
            else:
                icon = "●"
                state = "[已启用]"
                if source.startswith("MCP:"):
                    style = "#b39ddb"
                else:
                    style = "#6bcb77"

            label = Text(f"  {icon} {name} ({count} 工具) {state}", style=style)
            option_list.add_option(Option(label, id=name))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected):
        if event.option.id:
            self.agent.toggle_tool_group(event.option.id)
            self._render_groups()

    def action_dismiss_modal(self):
        self.dismiss()


class ToolApprovalScreen(ModalScreen[bool]):
    """工具审批弹窗：危险操作需要用户确认后才执行"""

    BINDINGS = [
        Binding("enter", "approve", "确认执行", priority=True),
        Binding("escape", "reject", "拒绝", priority=True),
    ]

    def __init__(self, tool_name: str, tool_args: dict, **kwargs):
        super().__init__(**kwargs)
        self.tool_name = tool_name
        self.tool_args = tool_args

    def compose(self) -> ComposeResult:
        args_str = json.dumps(self.tool_args, ensure_ascii=False, indent=2)
        with Vertical(id="approval-dialog"):
            yield Static("[bold #ff6b6b]⚠ 工具需要确认[/bold #ff6b6b]", id="approval-title")
            yield Static(f"[bold #ffd93d]工具: {self.tool_name}[/bold #ffd93d]", id="approval-tool")
            yield Static(f"[#c0c0c0]参数:[/#c0c0c0]", id="approval-args-label")
            with VerticalScroll(id="approval-args-scroll"):
                yield Static(Text(args_str, style="#e0e0e0"), id="approval-args")
            yield Static(
                "[bold #6bcb77]Enter = 确认执行[/bold #6bcb77]  |  [bold #ff6b6b]Esc = 拒绝[/bold #ff6b6b]",
                id="approval-footer",
            )

    def action_approve(self):
        self.dismiss(True)

    def action_reject(self):
        self.dismiss(False)

`````

--- **end of file: nb_agent/tui/widgets/screens.py** (project: nb_agent) --- 

---


--- **start of file: nb_agent/tui/widgets/tool_panel.py** (project: nb_agent) --- 


### 📄 Python File Metadata: `nb_agent/tui/widgets/tool_panel.py`

#### 📝 Module Docstring

`````
右侧工具/模型/MCP/Token 信息面板
`````

#### 📦 Imports

- `from textual.containers import Vertical`
- `from textual.containers import VerticalScroll`
- `from textual.app import ComposeResult`
- `from textual.widgets import OptionList`
- `from textual.widgets import RichLog`
- `from textual.widgets import Static`
- `from textual.widgets.option_list import Option`
- `from rich.text import Text`
- `from nb_agent.core import AgentCore`
- `from inputs import ClickableStatic`

#### 🏛️ Classes (1)

##### 📌 `class ToolPanel(Vertical)`
*Line: 19*

**Docstring:**
`````
右侧信息面板：分区展示，各区独立滚动
`````

**🔧 Constructor (`__init__`):**
- `def __init__(self, agent: AgentCore, **kwargs)`
  - **Parameters:**
    - `self`
    - `agent: AgentCore`
    - `**kwargs`

**Public Methods (4):**
- `def compose(self) -> ComposeResult`
- `def on_mount(self)`
- `def update_content(self, last_elapsed: float = 0.0)`
- `def on_option_list_option_selected(self, event: OptionList.OptionSelected)`


---

`````python
"""右侧工具/模型/MCP/Token 信息面板"""

from textual.containers import Vertical, VerticalScroll
from textual.app import ComposeResult
from textual.widgets import OptionList, RichLog, Static
from textual.widgets.option_list import Option
from rich.text import Text

from nb_agent.core import AgentCore
from .inputs import ClickableStatic


def _fmt_tokens(n: int) -> str:
    if n >= 1000:
        return f"{n / 1000:.1f}k"
    return str(n)


class ToolPanel(Vertical):
    """右侧信息面板：分区展示，各区独立滚动"""

    def __init__(self, agent: AgentCore, **kwargs):
        super().__init__(**kwargs)
        self.agent = agent

    def compose(self) -> ComposeResult:
        yield Static("", id="section-tokens")
        yield Static("", id="section-models-title")
        yield OptionList(id="section-models-list")
        yield Static("", id="section-mcp-title")
        yield OptionList(id="section-mcp-list")
        yield ClickableStatic("", id="section-tools-title")
        with VerticalScroll(id="section-tools-scroll"):
            yield ClickableStatic("", id="section-tools")

    def on_mount(self):
        self.update_content()

    def update_content(self, last_elapsed: float = 0.0):
        t = self.agent.get_token_usage()
        if t['total'] == 0:
            token_text = "[bold #ffd93d]✦ Token:[/bold #ffd93d] [#6b7394]等待对话...[/#6b7394]"
        else:
            elapsed_str = f" | 耗时{last_elapsed:.1f}s" if last_elapsed > 0 else ""
            last_info = f"本次 {_fmt_tokens(t['last_total'])}(入{_fmt_tokens(t['last_prompt'])}+出{_fmt_tokens(t['last_completion'])}){elapsed_str}"
            total_info = f"累计 {_fmt_tokens(t['total'])}(入{_fmt_tokens(t['total_prompt'])}+出{_fmt_tokens(t['total_completion'])})"
            token_text = (
                f"[bold #ffd93d]✦ Token[/bold #ffd93d]\n"
                f"  [#ffd93d]{last_info}[/#ffd93d]\n"
                f"  [#c0c0c0]{total_info}[/#c0c0c0]"
            )
        self.query_one("#section-tokens", Static).update(token_text)

        current_id = self.agent.get_model_name()
        grouped = self.agent.get_models_grouped()
        total = len(self.agent.available_models)
        self.query_one("#section-models-title", Static).update(
            f"[bold #4d96ff]模型 ({total})[/bold #4d96ff] [#6b7394]点击切换[/#6b7394]"
        )

        option_list = self.query_one("#section-models-list", OptionList)
        option_list.clear_options()
        for provider_name, models in grouped.items():
            option_list.add_option(Option(
                Text(f"── {provider_name} ──", style="#6b7394"), disabled=True
            ))
            for m in models:
                if m.id == current_id:
                    label = Text(f"▶ {m.id}", style="bold #00d4aa")
                else:
                    label = Text(f"  {m.id}", style="#8890a8")
                option_list.add_option(Option(label, id=m.id))

        mcp_status = self.agent.get_mcp_status()
        active_count = sum(1 for s in mcp_status if s["connected"] and not s.get("disabled"))
        self.query_one("#section-mcp-title", Static).update(
            f"[bold #ff922b]MCP Server ({active_count}/{len(mcp_status)})[/bold #ff922b] [#6b7394]点击切换[/#6b7394]"
        )
        mcp_list = self.query_one("#section-mcp-list", OptionList)
        mcp_list.clear_options()
        if not mcp_status:
            mcp_list.add_option(Option(Text("无配置", style="#6b7394"), disabled=True))
        else:
            for s in mcp_status:
                name = s["name"]
                if s.get("config_disabled"):
                    label = Text(f"  ○ {name} (配置禁用)", style="#6b7394")
                elif s.get("disabled"):
                    label = Text(f"  ◌ {name} (已禁用 {s['tools_count']}工具)", style="#8890a8")
                elif s["connected"]:
                    label = Text(f"  ● {name} ({s['tools_count']}工具)", style="#6bcb77")
                else:
                    err = s["error"][:20] if s["error"] else "失败"
                    label = Text(f"  ○ {name}: {err}", style="#ff6b6b")
                mcp_list.add_option(Option(label, id=f"mcp__{name}"))

        tools = self.agent.get_tools()
        enabled_count = sum(1 for t in tools if not t.get("disabled"))
        self.query_one("#section-tools-title", Static).update(
            f"[bold #6bcb77]工具 ({enabled_count}/{len(tools)})[/bold #6bcb77] [dim #6b7394]点击查看详情[/dim #6b7394]"
        )

        groups = {}
        for t in tools:
            group = t.get("group", "") or "(无分组)"
            if group not in groups:
                groups[group] = {"tools": [], "source": t["source"], "disabled": t.get("disabled", False)}
            groups[group]["tools"].append(t)

        tool_lines = []
        for group_name in sorted(groups.keys()):
            g = groups[group_name]
            src = g["source"]
            disabled = g["disabled"]
            disabled_tag = " [已禁用]" if disabled else ""
            if src.startswith("MCP:"):
                tool_lines.append(f"[dim #b39ddb]── {group_name}{disabled_tag} ──[/dim #b39ddb]")
            elif group_name == "(无分组)":
                tool_lines.append(f"[dim #6b7394]── {group_name} ──[/dim #6b7394]")
            else:
                tool_lines.append(f"[dim #6bcb77]── {group_name}{disabled_tag} ──[/dim #6bcb77]")
            for t in g["tools"]:
                func_name = t.get("func_name", t["name"])
                if disabled:
                    tool_lines.append(f"  [#6b7394]○ {func_name}[/#6b7394]")
                elif src.startswith("MCP:"):
                    tool_lines.append(f"  [#b39ddb]◆[/#b39ddb] [#c0c0c0]{func_name}[/#c0c0c0]")
                else:
                    tool_lines.append(f"  [#6bcb77]●[/#6bcb77] [#c0c0c0]{func_name}[/#c0c0c0]")
        self.query_one("#section-tools", Static).update("\n".join(tool_lines))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected):
        if not event.option.id:
            return
        opt_id = event.option.id

        if opt_id.startswith("mcp__"):
            server_name = opt_id[5:]
            status = self.agent.get_mcp_status()
            srv = next((s for s in status if s["name"] == server_name), None)
            if srv and srv.get("config_disabled"):
                self.app.notify(f"{server_name} 在配置中禁用，请修改 config.jsonc", severity="warning", timeout=3)
                return
            if srv and not srv["connected"]:
                self.app.notify(f"{server_name} 连接失败，无法切换", severity="warning", timeout=3)
                return
            enabled = self.agent.toggle_mcp_server(server_name)
            state = "启用" if enabled else "禁用"
            chat = self.app.query_one("#chat-panel", RichLog)
            chat.write(f"[#ff922b]✦ MCP [{server_name}] 已{state}[/#ff922b]")
            self.update_content()
            return

        model_id = opt_id
        old = self.agent.get_model_name()
        if model_id == old:
            return
        if self.agent.switch_model(model_id):
            chat = self.app.query_one("#chat-panel", RichLog)
            chat.write(f"\n[bold #ffd93d]✦ 模型已切换:[/bold #ffd93d] [#6b7394]{old}[/#6b7394] → [bold #00d4aa]{self.agent.get_model_name()}[/bold #00d4aa]")
            app = self.app
            if hasattr(app, '_update_subtitle'):
                app._update_subtitle()
            self.update_content()

`````

--- **end of file: nb_agent/tui/widgets/tool_panel.py** (project: nb_agent) --- 

---


--- **start of file: nb_agent/tui/widgets/__init__.py** (project: nb_agent) --- 


### 📄 Python File Metadata: `nb_agent/tui/widgets/__init__.py`

#### 📦 Imports

- `from inputs import ChatInput`
- `from inputs import ClickableStatic`
- `from tool_panel import ToolPanel`
- `from screens import ModelSelectScreen`
- `from screens import HelpScreen`
- `from screens import SessionSelectScreen`
- `from screens import ToolDetailScreen`
- `from screens import RoundsInputScreen`
- `from screens import ToolApprovalScreen`
- `from screens import ToolGroupToggleScreen`
- `from screens import SkillListScreen`
- `from screens import SkillContentScreen`
- `from screens import MentionSelectScreen`
- `from commands import AgentCommands`


---

`````python
from .inputs import ChatInput, ClickableStatic
from .tool_panel import ToolPanel
from .screens import (
    ModelSelectScreen,
    HelpScreen,
    SessionSelectScreen,
    ToolDetailScreen,
    RoundsInputScreen,
    ToolApprovalScreen,
    ToolGroupToggleScreen,
    SkillListScreen,
    SkillContentScreen,
    MentionSelectScreen,
)
from .commands import AgentCommands

__all__ = [
    "ChatInput",
    "ClickableStatic",
    "ToolPanel",
    "ModelSelectScreen",
    "HelpScreen",
    "SessionSelectScreen",
    "ToolDetailScreen",
    "RoundsInputScreen",
    "ToolApprovalScreen",
    "ToolGroupToggleScreen",
    "SkillListScreen",
    "SkillContentScreen",
    "MentionSelectScreen",
    "AgentCommands",
]

`````

--- **end of file: nb_agent/tui/widgets/__init__.py** (project: nb_agent) --- 

---

# markdown content namespace: nb_agent examples 


## nb_agent File Tree (relative dir: `examples`)


`````

└── examples
    ├── demo1
    │   └── main.py
    └── demo2
        ├── .nb_agent
        │   └── skills
        │       ├── daily-report
        │       │   └── SKILL.md
        │       └── meeting-notes
        │           └── SKILL.md
        ├── README.md
        ├── mcp_servers
        │   └── bookmark_server.py
        ├── notes
        │   ├── 20260527_190459_Celery 最简单 Demo - celery_app_py.md
        │   ├── 20260527_190459_Celery 最简单 Demo - run_py_调用任务_.md
        │   └── 20260527_190459_Celery 最简单 Demo - tasks_py.md
        ├── run.py
        ├── run_verbose.py
        └── tools
            ├── __init__.py
            ├── note_tools.py
            └── project_tools.py

`````

---


## nb_agent (relative dir: `examples`)  Included Files (total: 13 files)


- `examples/demo1/main.py`

- `examples/demo2/README.md`

- `examples/demo2/run.py`

- `examples/demo2/run_verbose.py`

- `examples/demo2/.nb_agent/skills/daily-report/SKILL.md`

- `examples/demo2/.nb_agent/skills/meeting-notes/SKILL.md`

- `examples/demo2/mcp_servers/bookmark_server.py`

- `examples/demo2/notes/20260527_190459_Celery 最简单 Demo - celery_app_py.md`

- `examples/demo2/notes/20260527_190459_Celery 最简单 Demo - run_py_调用任务_.md`

- `examples/demo2/notes/20260527_190459_Celery 最简单 Demo - tasks_py.md`

- `examples/demo2/tools/note_tools.py`

- `examples/demo2/tools/project_tools.py`

- `examples/demo2/tools/__init__.py`


---


--- **start of file: examples/demo1/main.py** (project: nb_agent) --- 

`````python
"""
nb_agent 综合示例 — 展示如何将 nb_agent 作为 Python 库导入使用

涵盖:
  1. 配置加载
  2. 自定义工具注册（@tool 装饰器 + register_tool 动态注册）
  3. Skills 系统（发现、查看、清单注入）
  4. 非流式对话（agent.chat）
  5. 流式对话（agent.chat_stream）
  6. 多会话管理（隔离、切换、历史）
  7. MCP 连接（如已配置）

用法:
    pip install -e .                        # 从 nb_agent 项目根目录安装
    export DEEPSEEK_API_KEY="your-key"      # 设置 API Key
    python main.py                          # 运行
"""

import asyncio
import json
from pathlib import Path

from pydantic import BaseModel, Field

from nb_agent.config import load_config
from nb_agent.core import AgentCore
from nb_agent.skills import SkillManager
from nb_agent.tools import tool


# ========================================================================
# 1. 自定义工具 — @tool 装饰器（import 时自动注册到全局 TOOL_REGISTRY）
# ========================================================================

class WeatherParams(BaseModel):
    city: str = Field(description="城市名称，如 '北京'、'上海'")


@tool
def get_weather(params: WeatherParams) -> str:
    """查询指定城市的天气（模拟数据）"""
    mock_data = {
        "北京": {"temp": 28, "weather": "晴", "humidity": 45},
        "上海": {"temp": 32, "weather": "多云", "humidity": 78},
        "深圳": {"temp": 35, "weather": "雷阵雨", "humidity": 85},
    }
    data = mock_data.get(params.city)
    if data:
        return f"{params.city}: {data['weather']}，{data['temp']}°C，湿度 {data['humidity']}%"
    return f"{params.city}: 暂无天气数据"


# ========================================================================
# 2. 自定义工具 — 普通函数（稍后通过 register_tool 动态注册）
# ========================================================================

def search_docs(query: str, top_k: int = 3) -> str:
    """模拟文档搜索"""
    results = [
        {"title": f"文档{i + 1}: 关于{query}的说明", "score": round(0.95 - i * 0.1, 2)}
        for i in range(top_k)
    ]
    return json.dumps(results, ensure_ascii=False)


# ========================================================================
# 辅助函数
# ========================================================================

def print_section(title: str):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def print_tools(agent: AgentCore):
    print("已注册工具:")
    for t in agent.get_tools():
        print(f"  [{t['source']:>6}] {t['name']}: {t['description'][:50]}")


def print_usage(agent: AgentCore, label: str = ""):
    usage = agent.get_token_usage()
    prefix = f"[{label}] " if label else ""
    print(f"  {prefix}Token: prompt={usage['last_prompt']}, "
          f"completion={usage['last_completion']}, "
          f"tools={usage['last_tool_calls']} | 累计={usage['total']}")


# ========================================================================
# 综合演示
# ========================================================================

async def demo_skills():
    """Part 1: Skills 系统（不需要 API Key）"""
    print_section("Part 1: Skills 系统")

    mgr = SkillManager(project_root=Path.cwd())
    mgr.discover()

    print("自动触发的 Skills:")
    for s in mgr.get_manifest():
        print(f"  - {s['name']}: {s['description'][:60]}...")

    print("\n全部 Skills（含手动模式）:")
    for s in mgr.get_all_skills():
        tag = " [仅手动]" if s["manual_only"] else ""
        print(f"  - {s['name']}{tag}")

    result = mgr.view_skill("code-review")
    if result["success"]:
        lines = result["content"].split("\n")[:3]
        print(f"\nview_skill('code-review') 前 3 行:")
        for line in lines:
            print(f"  {line}")


async def demo_chat(agent: AgentCore):
    """Part 2: 非流式对话 + 自动工具调用"""
    print_section("Part 2: 非流式对话")

    response = await agent.chat("现在几点了？北京天气怎么样？")

    print(f"回复: {response.text[:200]}")
    if response.tool_calls:
        print(f"\n工具调用链:")
        for tc in response.tool_calls:
            print(f"  → {tc.name}({tc.args}) [{tc.status}]")
            print(f"    结果: {tc.result[:80]}")
    print_usage(agent, "非流式")


async def demo_stream(agent: AgentCore):
    """Part 3: 流式对话"""
    print_section("Part 3: 流式对话")

    print("👤 帮我算一下 (123 + 456) * 789\n🤖 ", end="", flush=True)
    async for chunk in agent.chat_stream("帮我算一下 (123 + 456) * 789"):
        print(chunk, end="", flush=True)
    print()
    print_usage(agent, "流式")


async def demo_sessions(agent: AgentCore):
    """Part 4: 多会话管理"""
    print_section("Part 4: 多会话管理")

    session1_id = agent.session_id
    print(f"当前会话 ID: {session1_id}")

    agent.clear_history()
    session2_id = agent.session_id
    print(f"新建会话 ID: {session2_id}")
    print(f"会话已隔离: {session1_id != session2_id}")

    sessions = agent.get_session_list(limit=5)
    if sessions:
        print(f"\n最近 {len(sessions)} 个会话:")
        for s in sessions:
            print(f"  {s['id']} | {s['title'][:30]}")


async def demo_model_info(agent: AgentCore):
    """Part 5: 模型和 MCP 信息"""
    print_section("Part 5: 模型 & MCP 状态")

    print(f"当前模型: {agent.get_model_display_name()} ({agent.get_model_name()})")
    print(f"可用模型: {[m.id for m in agent.available_models]}")

    mcp_status = agent.get_mcp_status()
    if mcp_status:
        print(f"\nMCP Servers:")
        for s in mcp_status:
            state = "已连接" if s["connected"] else f"未连接({s['error'] or '已禁用'})"
            print(f"  {s['name']}: {state}, {s['tools_count']} 个工具")
    else:
        print("\nMCP: 未配置（在 config.jsonc 中添加 mcp 配置即可）")


async def main():
    print("nb_agent 综合示例")
    print(f"版本: {__import__('nb_agent').__version__}")
    print("-" * 60)

    # --- Skills（不需要 API Key） ---
    await demo_skills()

    # --- 加载配置、创建 Agent ---
    config = load_config()
    agent = AgentCore(config)

    # 动态注册自定义工具（方式 2）
    agent.register_tool(
        name="search_docs",
        func=search_docs,
        description="搜索知识库文档",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"},
                "top_k": {"type": "integer", "description": "返回数量", "default": 3},
            },
            "required": ["query"],
        },
    )

    print_tools(agent)

    # --- 连接 MCP ---
    await agent.connect_mcp()

    try:
        await demo_model_info(agent)

        # 以下需要有效的 API Key
        if agent.current_model and agent.current_model.api_key:
            await demo_chat(agent)
            await demo_stream(agent)
            await demo_sessions(agent)
        else:
            print_section("跳过对话演示")
            print("未检测到有效的 API Key，跳过对话演示。")
            print("请设置环境变量（如 DEEPSEEK_API_KEY）并在 config.jsonc 中配置 provider。")

    finally:
        await agent.disconnect_mcp()

    print_section("完成")
    print("所有演示已结束。更多用法请参考 nb_agent 的 README.md。")


if __name__ == "__main__":
    asyncio.run(main())

`````

--- **end of file: examples/demo1/main.py** (project: nb_agent) --- 

---


--- **start of file: examples/demo2/README.md** (project: nb_agent) --- 

`````markdown
# 智能笔记助手 — nb_agent 项目级演示

一个基于 nb_agent 的智能笔记管理项目，展示如何开发自定义 Tools + Skills 并集成到 TUI。

## 项目结构

```
demo2/
├── config.jsonc                  # nb_agent 配置（模型、MCP、审批）
├── run.py                        # 入口脚本（极简版：4 行代码启动）
├── run_verbose.py                # 入口脚本（详细版：启动前打印加载信息）
├── tools/                        # 自定义工具（@tool 装饰器）
│   ├── __init__.py               # 导出（import 即注册）
│   ├── note_tools.py             # 笔记管理：增删查改
│   └── project_tools.py          # 项目统计：文件数/代码行数
├── mcp_servers/                  # 自定义 MCP Server
│   └── bookmark_server.py        # 书签管理 MCP（stdio 方式）
├── .nb_agent/skills/             # 自定义 Skills
│   ├── meeting-notes/SKILL.md    # 会议纪要生成模板
│   └── daily-report/SKILL.md     # 日报生成模板
├── data/                         # MCP Server 数据目录
│   └── bookmarks.json            # 书签数据（自动生成）
├── notes/                        # 笔记数据存储
└── README.md
```

## 快速开始

```bash
# 1. 安装 nb_agent
cd D:/codes/nb_agent
pip install -e .

# 2. 进入项目目录
cd examples/demo2

# 3. 启动（极简版）
python run.py

# 或者启动详细版（打印工具/Skills/MCP/模型信息后再进入 TUI）
python run_verbose.py
```

## 自定义内容

### Tools（@tool 装饰器）

在 `tools/` 目录下用 `@tool` 装饰器定义工具，import 即自动注册：

- `create_note` — 创建笔记（标题、内容、标签）
- `search_notes` — 按关键词/标签搜索笔记
- `list_notes` — 列出最近的笔记
- `read_note` — 读取某条笔记全文
- `delete_note` — 删除笔记（配置了审批，需用户确认）
- `project_stats` — 项目文件统计（行数、类型分布）
- `find_files` — 按 glob 模式搜索文件

### Skills（SKILL.md）

在 `.nb_agent/skills/` 下创建目录和 `SKILL.md`，AI 自动发现：

- `meeting-notes` — 会议纪要结构化模板
- `daily-report` — 日报生成模板

### MCP Server（书签管理）

在 `mcp_servers/bookmark_server.py` 中编写了一个完整的 MCP Server，
通过 stdio 方式被 nb_agent 自动连接。提供 4 个工具：

- `add_bookmark` — 保存网页书签
- `search_bookmarks` — 搜索书签
- `list_bookmarks` — 列出所有书签
- `delete_bookmark` — 删除书签

MCP 工具和 @tool 工具的区别：
- **@tool（进程内）**：直接运行在 nb_agent 进程中，import 即注册
- **MCP（独立进程）**：运行在独立子进程中，通过 stdin/stdout 通信
- MCP 适合：依赖独立环境的工具、需要长期运行的服务、跨语言工具

### 审批机制

`delete_note` 被配置为危险工具（`config.jsonc` 中的 `dangerous_tools`），
AI 调用时会弹出确认对话框，用户手动审批后才会执行。

## TUI 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+J` | 发送消息 |
| `Ctrl+N` | 新建会话 |
| `Ctrl+M` | 切换模型 |
| `Ctrl+T` | 工具面板 |
| `Ctrl+P` | 命令面板 |
| `Ctrl+Q` | 退出 |

## 三种扩展方式对比

| 特性 | @tool（内置工具） | MCP Server | Skills |
|------|-------------------|------------|--------|
| 运行方式 | 进程内 | 独立进程 | Markdown 指南 |
| 注册方式 | import 即注册 | 配置 config.jsonc | 放入 .nb_agent/skills/ |
| 适合场景 | 简单本地操作 | 复杂/跨语言服务 | 流程模板/最佳实践 |
| 本项目示例 | 笔记管理、项目统计 | 书签管理 | 会议纪要、日报 |

## 使用场景

1. **创建笔记** [Tool]: "帮我记录一下今天的学习笔记，主题是 Python 异步编程"
2. **搜索笔记** [Tool]: "搜索关于 Python 的笔记"
3. **保存书签** [MCP]: "帮我保存这个链接 https://docs.python.org，标签是 python,文档"
4. **搜索书签** [MCP]: "找找关于 Python 的书签"
5. **会议纪要** [Skill]: "帮我写一个会议纪要"（AI 会自动调用 meeting-notes Skill）
6. **日报生成** [Skill]: "帮我写今天的日报"（AI 会调用 daily-report Skill）
7. **项目统计** [Tool]: "看看当前项目有多少文件和代码"

`````

--- **end of file: examples/demo2/README.md** (project: nb_agent) --- 

---


--- **start of file: examples/demo2/run.py** (project: nb_agent) --- 

`````python
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

`````

--- **end of file: examples/demo2/run.py** (project: nb_agent) --- 

---


--- **start of file: examples/demo2/run_verbose.py** (project: nb_agent) --- 

`````python
"""
智能笔记助手 — 详细版入口（启动前打印所有加载信息）

和 run.py 功能完全相同，只是启动前额外打印：
  - 已注册的工具列表
  - 已发现的 Skills
  - MCP Server 状态
  - 模型信息

适合调试和学习 nb_agent 的内部机制。
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
config["_project_root"] = os.getcwd()

print("=" * 50)
print("  智能笔记助手 (基于 nb_agent)")
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

print(f"\n笔记目录: {os.path.abspath('notes')}")
notes_count = len(list(Path("notes").glob("*.md")))
print(f"现有笔记: {notes_count} 条")

print("\n启动 TUI...\n")
AgentApp(config).run()

`````

--- **end of file: examples/demo2/run_verbose.py** (project: nb_agent) --- 

---


--- **start of file: examples/demo2/.nb_agent/skills/daily-report/SKILL.md** (project: nb_agent) --- 

`````markdown
---
name: daily-report
description: >-
  生成每日工作日报。当用户提到写日报、工作总结、daily report、
  今日工作、或要求汇总今天完成的任务时使用。
---

# 日报生成 Skill

帮用户整理今天的工作内容，生成结构化日报。

## 输出模板

使用以下模板，用 `create_note` 工具保存，tags 设为 `daily`：

```markdown
# 工作日报 — YYYY-MM-DD

## 今日完成

1. **[任务名]** — 具体描述
2. **[任务名]** — 具体描述

## 进行中

1. **[任务名]** — 进度描述，预计完成时间
   - 阻塞项（如有）：...

## 明日计划

1. [计划任务]
2. [计划任务]

## 备注

（其他需要记录的事项）
```

## 处理流程

1. 先调用 `list_notes` 查看今天已有的笔记作为参考
2. 询问用户今天完成了什么、正在做什么、明天计划做什么
3. 按模板整理，语言简洁，重点突出
4. 用 `create_note` 保存，标题格式：`日报-YYYY-MM-DD`

`````

--- **end of file: examples/demo2/.nb_agent/skills/daily-report/SKILL.md** (project: nb_agent) --- 

---


--- **start of file: examples/demo2/.nb_agent/skills/meeting-notes/SKILL.md** (project: nb_agent) --- 

`````markdown
---
name: meeting-notes
description: >-
  生成结构化的会议纪要。当用户提到会议记录、会议纪要、meeting notes、
  或要求整理会议内容时使用。
---

# 会议纪要 Skill

将用户的会议信息整理为结构化的会议纪要。

## 输出模板

使用以下模板生成纪要，用 `create_note` 工具保存，tags 设为 `meeting`：

```markdown
# [会议主题]

**日期**: YYYY-MM-DD
**参与者**: 张三, 李四, ...
**会议时长**: X 小时

## 议题与讨论

### 1. [议题名称]
- 背景：...
- 讨论要点：...
- 结论：...

### 2. [议题名称]
...

## 待办事项

| 编号 | 任务 | 负责人 | 截止日期 |
|------|------|--------|----------|
| 1 | ... | ... | ... |

## 下次会议

- 时间：
- 预定议题：
```

## 处理流程

1. 询问用户会议的主题、参与者、讨论内容
2. 如果用户提供了录音转写文本，从中提取关键信息
3. 按模板整理输出
4. 用 `create_note` 工具保存，标题格式：`会议纪要-[主题]-[日期]`
5. 确认是否需要补充或修改

`````

--- **end of file: examples/demo2/.nb_agent/skills/meeting-notes/SKILL.md** (project: nb_agent) --- 

---


--- **start of file: examples/demo2/mcp_servers/bookmark_server.py** (project: nb_agent) --- 

`````python
"""
书签管理 MCP Server — 通过 MCP 协议提供书签增删查功能

展示如何用 FastMCP 编写一个 MCP Server，
只需一个 @mcp.tool() 装饰器即可定义工具，
schema 从函数签名 + Pydantic Field 自动生成。

配置方式（在 config.jsonc 的 mcp 节）：
  "bookmark": {
    "type": "local",
    "command": ["python", "mcp_servers/bookmark_server.py"],
    "enabled": true
  }
"""

import json
from datetime import datetime
from pathlib import Path

from pydantic import Field
from mcp.server.fastmcp import FastMCP

BOOKMARKS_FILE = Path(__file__).parent.parent / "data" / "bookmarks.json"

mcp = FastMCP("bookmark-manager")


def _load_bookmarks() -> list:
    if BOOKMARKS_FILE.exists():
        return json.loads(BOOKMARKS_FILE.read_text(encoding="utf-8"))
    return []


def _save_bookmarks(bookmarks: list):
    BOOKMARKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    BOOKMARKS_FILE.write_text(
        json.dumps(bookmarks, ensure_ascii=False, indent=2), encoding="utf-8"
    )


@mcp.tool()
def add_bookmark(
    url: str = Field(description="网页 URL"),
    title: str = Field(description="书签标题"),
    tags: str = Field(default="", description="逗号分隔的标签，如 'python,教程'"),
) -> str:
    """保存一个网页书签"""
    bookmarks = _load_bookmarks()

    for bm in bookmarks:
        if bm["url"] == url:
            return f"书签已存在: {url}"

    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    bookmarks.append({
        "url": url,
        "title": title,
        "tags": tag_list,
        "created": datetime.now().isoformat(),
    })
    _save_bookmarks(bookmarks)
    return f"书签已保存: {title} ({url})"


@mcp.tool()
def search_bookmarks(
    keyword: str = Field(description="搜索关键词"),
    tag: str = Field(default="", description="按标签过滤（可选）"),
) -> str:
    """搜索书签（按关键词或标签）"""
    bookmarks = _load_bookmarks()
    kw = keyword.lower()
    results = []

    for bm in bookmarks:
        if tag and tag.lower() not in [t.lower() for t in bm.get("tags", [])]:
            continue
        if kw in bm["title"].lower() or kw in bm["url"].lower():
            results.append(bm)

    if not results:
        return f"未找到包含 '{keyword}' 的书签"
    return json.dumps(results[:20], ensure_ascii=False, indent=2)


@mcp.tool()
def list_bookmarks(
    limit: int = Field(default=20, description="返回数量上限"),
) -> str:
    """列出所有书签"""
    bookmarks = _load_bookmarks()
    if not bookmarks:
        return "暂无书签"
    display = bookmarks[-limit:]
    display.reverse()
    return json.dumps(display, ensure_ascii=False, indent=2)


@mcp.tool()
def delete_bookmark(
    url: str = Field(description="要删除的书签 URL"),
) -> str:
    """删除一个书签（按 URL 匹配）"""
    bookmarks = _load_bookmarks()
    original_count = len(bookmarks)
    bookmarks = [bm for bm in bookmarks if bm["url"] != url]
    if len(bookmarks) == original_count:
        return f"未找到书签: {url}"
    _save_bookmarks(bookmarks)
    return f"已删除书签: {url}"


if __name__ == "__main__":
    mcp.run(transport="stdio")

`````

--- **end of file: examples/demo2/mcp_servers/bookmark_server.py** (project: nb_agent) --- 

---


--- **start of file: examples/demo2/notes/20260527_190459_Celery 最简单 Demo - celery_app_py.md** (project: nb_agent) --- 

`````markdown
---
title: Celery 最简单 Demo - celery_app.py
created: 2026-05-27T19:04:59.408895
tags: celery, demo, python
---

from celery import Celery

# 创建 Celery 应用
# broker: 消息代理（这里用 Redis）
# backend: 结果存储（这里用 Redis）
app = Celery(
    'demo',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

`````

--- **end of file: examples/demo2/notes/20260527_190459_Celery 最简单 Demo - celery_app_py.md** (project: nb_agent) --- 

---


--- **start of file: examples/demo2/notes/20260527_190459_Celery 最简单 Demo - run_py_调用任务_.md** (project: nb_agent) --- 

`````markdown
---
title: Celery 最简单 Demo - run.py（调用任务）
created: 2026-05-27T19:04:59.413418
tags: celery, demo, python
---

from tasks import add, hello

# ──────────────────────────────
# 1️⃣ 异步发送任务（不等待结果）
# ──────────────────────────────
print("🚀 发送加法任务...")
result = add.delay(3, 5)
print(f"   任务 ID: {result.id}")
print(f"   任务状态: {result.status}")

# ──────────────────────────────
# 2️⃣ 等待并获取结果
# ──────────────────────────────
print("\n⏳ 等待结果...")
answer = result.get(timeout=10)  # 最多等10秒
print(f"🎉 3 + 5 = {answer}")

# ──────────────────────────────
# 3️⃣ 另一个任务
# ──────────────────────────────
print("\n👋 发送打招呼任务...")
hello_result = hello.delay("Celery")
print(f"   {hello_result.get(timeout=5)}")

print("\n✅ 全部完成！")

`````

--- **end of file: examples/demo2/notes/20260527_190459_Celery 最简单 Demo - run_py_调用任务_.md** (project: nb_agent) --- 

---


--- **start of file: examples/demo2/notes/20260527_190459_Celery 最简单 Demo - tasks_py.md** (project: nb_agent) --- 

`````markdown
---
title: Celery 最简单 Demo - tasks.py
created: 2026-05-27T19:04:59.411408
tags: celery, demo, python
---

from celery_app import app
import time

@app.task
def add(x, y):
    """最简单的加法任务"""
    print(f"📝 正在计算: {x} + {y}")
    time.sleep(2)  # 模拟耗时操作
    result = x + y
    print(f"✅ 计算结果: {result}")
    return result

@app.task
def hello(name):
    """打招呼任务"""
    return f"Hello, {name}!"

`````

--- **end of file: examples/demo2/notes/20260527_190459_Celery 最简单 Demo - tasks_py.md** (project: nb_agent) --- 

---


--- **start of file: examples/demo2/tools/note_tools.py** (project: nb_agent) --- 

`````python
"""
笔记管理工具 — 增删查改笔记

每个工具通过 @tool 装饰器自动注册到 nb_agent。
AI 会根据用户意图自主决定调用哪个工具。
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from nb_agent.tools import tool

NOTES_DIR = Path(__file__).parent.parent / "notes"
NOTES_DIR.mkdir(parents=True, exist_ok=True)


class CreateNoteParams(BaseModel):
    title: str = Field(description="笔记标题")
    content: str = Field(description="笔记内容（支持 Markdown）")
    tags: str = Field(default="", description="逗号分隔的标签，如 'work,meeting,todo'")


@tool(group="note")
def create_note(params: CreateNoteParams) -> str:
    """创建一条笔记，保存到本地文件"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = "".join(c if c.isalnum() or c in "-_ " else "_" for c in params.title)
    filename = f"{ts}_{safe_title}.md"
    filepath = NOTES_DIR / filename

    tags_line = ""
    if params.tags:
        tag_list = [t.strip() for t in params.tags.split(",") if t.strip()]
        tags_line = f"tags: {', '.join(tag_list)}\n"

    note_content = (
        f"---\n"
        f"title: {params.title}\n"
        f"created: {datetime.now().isoformat()}\n"
        f"{tags_line}"
        f"---\n\n"
        f"{params.content}\n"
    )

    filepath.write_text(note_content, encoding="utf-8")
    return f"笔记已创建: {filepath.name}"


class SearchNotesParams(BaseModel):
    keyword: str = Field(description="搜索关键词（在标题和内容中查找）")
    tag: str = Field(default="", description="按标签过滤（可选）")


@tool(group="note")
def search_notes(params: SearchNotesParams) -> str:
    """搜索笔记，按关键词和标签过滤"""
    results = []
    keyword = params.keyword.lower()

    for f in sorted(NOTES_DIR.glob("*.md"), reverse=True):
        content = f.read_text(encoding="utf-8")
        title = _extract_field(content, "title") or f.stem
        tags = _extract_field(content, "tags") or ""
        created = _extract_field(content, "created") or ""

        if params.tag and params.tag.lower() not in tags.lower():
            continue

        if keyword in content.lower() or keyword in title.lower():
            body = content.split("---", 2)[-1].strip() if "---" in content else content
            preview = body[:100].replace("\n", " ")
            results.append({
                "file": f.name,
                "title": title,
                "tags": tags,
                "created": created[:19],
                "preview": preview,
            })

    if not results:
        return f"未找到包含 '{params.keyword}' 的笔记"
    return json.dumps(results[:10], ensure_ascii=False, indent=2)


class ListNotesParams(BaseModel):
    limit: int = Field(default=10, description="返回的笔记数量上限")


@tool(group="note")
def list_notes(params: ListNotesParams) -> str:
    """列出最近的笔记"""
    files = sorted(NOTES_DIR.glob("*.md"), reverse=True)
    if not files:
        return "暂无笔记"

    notes = []
    for f in files[:params.limit]:
        content = f.read_text(encoding="utf-8")
        title = _extract_field(content, "title") or f.stem
        tags = _extract_field(content, "tags") or ""
        created = _extract_field(content, "created") or ""
        notes.append({
            "file": f.name,
            "title": title,
            "tags": tags,
            "created": created[:19],
        })
    return json.dumps(notes, ensure_ascii=False, indent=2)


class ReadNoteParams(BaseModel):
    filename: str = Field(description="笔记文件名，如 '20260527_143000_会议记录.md'")


@tool(group="note")
def read_note(params: ReadNoteParams) -> str:
    """读取某条笔记的完整内容"""
    filepath = NOTES_DIR / params.filename
    if not filepath.exists():
        return f"文件不存在: {params.filename}"
    return filepath.read_text(encoding="utf-8")


class DeleteNoteParams(BaseModel):
    filename: str = Field(description="要删除的笔记文件名")


@tool(group="note")
def delete_note(params: DeleteNoteParams) -> str:
    """删除一条笔记（危险操作，需要用户确认）"""
    filepath = NOTES_DIR / params.filename
    if not filepath.exists():
        return f"文件不存在: {params.filename}"
    filepath.unlink()
    return f"已删除: {params.filename}"


def _extract_field(content: str, field_name: str) -> Optional[str]:
    """从 YAML frontmatter 中提取字段值"""
    for line in content.split("\n"):
        if line.startswith(f"{field_name}:"):
            return line[len(field_name) + 1:].strip()
    return None

`````

--- **end of file: examples/demo2/tools/note_tools.py** (project: nb_agent) --- 

---


--- **start of file: examples/demo2/tools/project_tools.py** (project: nb_agent) --- 

`````python
"""
项目统计工具 — 分析当前项目的文件结构和代码统计

展示如何编写不依赖外部服务的本地工具。
"""

import os
from collections import Counter, defaultdict
from pathlib import Path

from pydantic import BaseModel, Field

from nb_agent.tools import tool

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", ".mypy_cache", ".pytest_cache"}


class ProjectStatsParams(BaseModel):
    directory: str = Field(default=".", description="项目目录路径，默认当前目录")


@tool(group="project")
def project_stats(params: ProjectStatsParams) -> str:
    """统计项目的文件数量、代码行数、文件类型分布"""
    root = Path(params.directory).resolve()
    if not root.is_dir():
        return f"目录不存在: {params.directory}"

    ext_counter = Counter()
    lines_counter = defaultdict(int)
    total_files = 0
    total_lines = 0
    total_size = 0

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in filenames:
            fpath = Path(dirpath) / fname
            ext = fpath.suffix.lower() or "(无后缀)"
            ext_counter[ext] += 1
            total_files += 1
            total_size += fpath.stat().st_size

            if ext in {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".md", ".yaml", ".yml", ".json", ".toml"}:
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        line_count = sum(1 for _ in f)
                        lines_counter[ext] += line_count
                        total_lines += line_count
                except (OSError, UnicodeDecodeError):
                    pass

    report = [
        f"项目: {root.name}",
        f"路径: {root}",
        f"文件总数: {total_files}",
        f"代码总行数: {total_lines:,}",
        f"总大小: {_format_size(total_size)}",
        "",
        "文件类型分布 (Top 10):",
    ]
    for ext, count in ext_counter.most_common(10):
        lines = lines_counter.get(ext, 0)
        lines_info = f" ({lines:,} 行)" if lines > 0 else ""
        report.append(f"  {ext:>10}: {count:>5} 个{lines_info}")

    return "\n".join(report)


class FindFilesParams(BaseModel):
    pattern: str = Field(description="文件名匹配模式（支持 glob），如 '*.py' 或 'test_*.py'")
    directory: str = Field(default=".", description="搜索目录，默认当前目录")
    max_results: int = Field(default=20, description="最大返回数量")


@tool(group="project")
def find_files(params: FindFilesParams) -> str:
    """在项目中搜索匹配的文件"""
    root = Path(params.directory).resolve()
    if not root.is_dir():
        return f"目录不存在: {params.directory}"

    results = []
    for fpath in root.rglob(params.pattern):
        if any(skip in fpath.parts for skip in SKIP_DIRS):
            continue
        rel = fpath.relative_to(root)
        results.append(str(rel))
        if len(results) >= params.max_results:
            break

    if not results:
        return f"未找到匹配 '{params.pattern}' 的文件"

    return f"找到 {len(results)} 个文件:\n" + "\n".join(f"  {r}" for r in results)


def _format_size(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"

`````

--- **end of file: examples/demo2/tools/project_tools.py** (project: nb_agent) --- 

---


--- **start of file: examples/demo2/tools/__init__.py** (project: nb_agent) --- 

`````python
"""
自定义工具包 — import 即自动注册到 nb_agent 的 TOOL_REGISTRY

使用 @tool 装饰器的工具在 import 时自动注册，
无需手动调用 register_tool()。
"""

from . import note_tools    # noqa: F401
from . import project_tools  # noqa: F401

`````

--- **end of file: examples/demo2/tools/__init__.py** (project: nb_agent) --- 

---

