# nb_agent 规划 v3

> 最后更新: 2026-05-27
> 状态: 规划中

## 一、定位

**手写 ReAct Agent 框架 + 赛博朋克 TUI**

不依赖 LangChain，用纯 Python 实现 LLM ↔ Tool 循环。
支持三种扩展方式：**Tools（内置）+ MCP（外部）+ Skills（指导手册）**。

nb_agent 是**通用 Agent**——不专门做 coding，不专门做 RAG。
Coding 能力通过用户配置 MCP（如 Serena）获得，RAG 能力通过 MCP（如 nb_agentic_rag）获得。
也可以单纯聊天、问生活娱乐问题。

### 核心价值

1. **教学价值**：手写 Agent 循环，理解 Cursor / OpenCode / Claude Code 的底层原理
2. **三种扩展方式**：Tools + MCP + Skills 正交设计
3. **生产级特性**：上下文裁剪、指数退避重试、危险操作审批、会话持久化
4. **赛博朋克 TUI**：流式输出 + 思考链 + 模型切换 + MCP 状态 + Token 统计

### 和 learn_agent 的关系

nb_agent 从 `learn_agent` 拆分独立，新增 Skills 系统，重新组织项目结构。

---

## 二、架构

**TUI 直接 import AgentCore，同进程，无 HTTP 中间层。**

```
┌──────────────────────────────────────────────────────────┐
│  TUI (Textual)                                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │ 聊天区    │ │ 输入框   │ │ 工具面板  │ │ 状态栏    │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
│           │                                               │
│           │ 直接 import（同进程）                          │
│           ▼                                               │
│  ┌────────────────────────────────────────────────┐       │
│  │  AgentCore (ReAct 循环)                         │       │
│  │  ├── ToolRegistry    (内置 tools: @tool 装饰器) │       │
│  │  ├── MCPManager      (外部 tools: MCP 协议)    │       │
│  │  ├── SkillManager    (指导手册: SKILL.md)      │       │
│  │  ├── SessionStore    (会话持久化: SQLModel)     │       │
│  │  └── ApprovalEngine  (危险操作审批)             │       │
│  └────────────────────────────────────────────────┘       │
│           │                                               │
│           │ MCP 协议 (stdio / SSE / HTTP)                 │
│           ▼                                               │
│  ┌────────┐ ┌──────────────┐ ┌────────┐                 │
│  │ Serena │ │nb_agentic_rag│ │ 其他MCP│                 │
│  │(coding)│ │   (RAG)      │ │ Server │                 │
│  └────────┘ └──────────────┘ └────────┘                 │
└──────────────────────────────────────────────────────────┘
```

---

## 三、三种扩展方式

### 3.1 Tools — 内置可执行工具

用 `@tool` 装饰器注册 Python 函数，Pydantic 自动生成 JSON Schema。

```python
from nb_agent.tools import tool

@tool("获取当前时间")
def get_current_time(timezone: str = "Asia/Shanghai") -> str:
    """返回指定时区的当前时间。"""
    ...
```

内置工具（随包发布，不需要配置）：
- `get_current_time` — 获取当前时间
- `calculate` — 数学计算
- `view_skill` — 查看 Skill 详情（Skills 系统内置）

### 3.2 MCP — 外部工具协议

通过 MCP 协议接入外部工具，用户在 `config.jsonc` 中配置。

```jsonc
// config.jsonc
{
  "mcp": {
    "serena": {
      "command": "serena",
      "args": ["start-mcp-server", "--project-from-cwd"],
      "enabled": true
    },
    "rag": {
      "command": "uvx",
      "args": ["nb_agentic_rag"],
      "env": { "NB_RAG_API_KEY": "sk-xxx" },
      "enabled": true
    }
  }
}
```

MCPManager 支持：
- stdio / SSE / streamable-http 三种传输
- 运行时启禁 MCP Server（TUI 快捷键）
- 工具命名空间防冲突：`mcp__serena__find_symbol`

### 3.3 Skills — Markdown 指导手册

Skills ≠ 提示词，也 ≠ 可执行代码。
Skill 是**结构化的 Markdown 指导手册**，教 AI "怎么做"某类任务。

**三者正交：**
- **Tool** → AI "能做什么"（可执行代码 / MCP 工具）
- **Skill** → AI "怎么做"（Markdown 指导手册）
- **System Prompt** → AI "是谁"（人设 / 行为约束）

#### SKILL.md 格式（兼容 Cursor / Claude Code）

```markdown
---
name: code-review
description: "审查代码质量、安全性和最佳实践"
paths: "src/**/*.py,tests/**/*.py"
---

# 代码审查 Skill

## 审查流程
1. 读取变更文件列表
2. 每个文件检查：安全漏洞、性能问题、代码规范
3. 输出结构化审查报告

## 约束
- 不修改代码，只提出建议
```

#### Progressive Disclosure（渐进式披露）

```
启动时: SkillManager.discover() 只读 frontmatter（name + description）→ 几个 token
需要时: Agent 调 view_skill("code-review") 按需加载完整内容 → 几百 token
执行时: Agent 按 SKILL.md 的指导执行任务
```

#### Skill 目录层级（三层优先级）

```
优先级: 项目级 > 全局级 > 内置

1. 项目级: .nb_agent/skills/        (项目根目录, 同名覆盖内置)
2. 全局级: ~/.nb_agent/skills/       (用户 home 目录)
3. 内置:   nb_agent/skills/builtin/  (随包发布)
```

#### SkillManager

```python
class SkillManager:
    def discover(self):
        """启动时扫描所有 skill 目录，只读 frontmatter"""

    def get_manifest(self) -> list[dict]:
        """返回所有 skill 的 name + description，注入 system prompt"""

    def view_skill(self, skill_name: str) -> str:
        """内置工具: Agent 按需调用，加载完整 SKILL.md 内容"""

    def match_skills(self, file_paths: list[str]) -> list[str]:
        """根据 paths glob 自动匹配相关 skills"""
```

`view_skill` 注册为内置工具，Agent 在需要时自主决定调用。

---

## 四、目录结构

```
nb_agent/
├── pyproject.toml
├── README.md
├── LICENSE                        # MIT
├── config.example.jsonc           # 脱敏配置模板
│
├── nb_agent/
│   ├── __init__.py                # __version__
│   ├── __main__.py                # python -m nb_agent
│   ├── main.py                    # CLI 入口
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   └── loader.py              # JSONC 配置 (CLI > ENV > JSONC > 默认值)
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── agent.py               # AgentCore — ReAct 循环核心
│   │   ├── models.py              # ModelInfo + Provider 管理
│   │   ├── context.py             # 上下文窗口管理 (token 估算 + trim)
│   │   └── retry.py               # LLM 调用重试 (指数退避)
│   │
│   ├── tools/
│   │   ├── __init__.py            # TOOL_REGISTRY, @tool
│   │   ├── base.py                # @tool 装饰器 + Pydantic schema
│   │   └── builtin.py             # get_current_time, calculate
│   │
│   ├── mcp/
│   │   ├── __init__.py
│   │   └── client.py              # MCPManager (多 Server + 运行时启禁)
│   │
│   ├── skills/
│   │   ├── __init__.py
│   │   ├── manager.py             # SkillManager — 发现/加载/view_skill
│   │   └── builtin/               # 内置 skills (随包发布)
│   │       ├── code-review/
│   │       │   └── SKILL.md
│   │       ├── explain-code/
│   │       │   └── SKILL.md
│   │       └── refactor/
│   │           └── SKILL.md
│   │
│   ├── session/
│   │   ├── __init__.py
│   │   ├── models.py              # SQLModel 模型 (ChatSession, Message)
│   │   └── store.py               # SessionStore (SQLModel, 默认 SQLite)
│   │
│   ├── approval/
│   │   ├── __init__.py
│   │   └── engine.py              # ApprovalEngine + 规则
│   │
│   └── tui/
│       ├── __init__.py
│       ├── app.py                 # AgentApp 主应用 (Textual)
│       ├── widgets/               # 拆分组件
│       │   ├── __init__.py
│       │   ├── chat_view.py       # 聊天消息显示
│       │   ├── input_box.py       # 输入框
│       │   ├── tool_panel.py      # 右侧工具面板 (工具列表 + Token + MCP)
│       │   └── dialogs.py         # 弹窗 (模型/帮助/会话切换)
│       └── styles.tcss            # CSS 样式 (赛博朋克暗色主题)
│
├── .nb_agent/skills/              # 项目级 skills (示例)
│   └── example-skill/
│       └── SKILL.md
│
└── tests/
    ├── test_agent_core.py
    ├── test_mcp_client.py
    ├── test_session.py
    ├── test_skills.py
    └── test_tools.py
```

---

## 五、配置设计

### config.jsonc 结构

```jsonc
{
  // LLM 连接
  "provider": {
    "api_key": "${OPENAI_API_KEY}",        // 支持环境变量引用
    "base_url": "https://api.deepseek.com/v1",
    "default_model": "deepseek-chat"
  },

  // 可用模型列表 (TUI 中 Ctrl+M 切换)
  "models": [
    { "id": "deepseek-chat", "name": "DeepSeek V3", "max_tokens": 8192 },
    { "id": "deepseek-reasoner", "name": "DeepSeek R1", "max_tokens": 8192 }
  ],

  // Agent 行为
  "agent": {
    "system_prompt": "You are a helpful AI assistant.",
    "max_rounds": 20,
    "temperature": 0.7
  },

  // MCP Server 配置
  "mcp": {
    "serena": {
      "command": "serena",
      "args": ["start-mcp-server", "--project-from-cwd"],
      "enabled": false
    },
    "rag": {
      "command": "uvx",
      "args": ["nb_agentic_rag"],
      "env": { "NB_RAG_API_KEY": "sk-xxx" },
      "enabled": false
    }
  },

  // 审批规则
  "approval": {
    "dangerous_tools": ["execute_shell_command", "mcp__serena__replace_content"],
    "auto_approve": false
  },

  // 会话存储
  "session": {
    "db_path": "~/.nb_agent/sessions.db"
  }
}
```

### 配置加载优先级

```
CLI 参数 > 环境变量 > 项目级 ./config.jsonc > 全局 ~/.nb_agent/config.jsonc > 默认值
```

---

## 六、CLI 入口

```bash
nb_agent                                # 启动 TUI
nb_agent --config ./my_config.jsonc     # 指定配置
nb_agent run "帮我分析这段代码的性能"    # 非交互模式: 执行一次输出结果
nb_agent run -f prompt.txt              # 从文件读取 prompt
nb_agent sessions list                  # 列出历史会话
nb_agent sessions show <id>             # 查看历史会话内容
```

### TUI 快捷键

| 快捷键 | 功能 |
|--------|------|
| Ctrl+M | 切换模型 |
| Ctrl+S | 切换/新建会话 |
| Ctrl+T | 工具面板显隐 |
| Ctrl+P | MCP Server 启禁 |
| Ctrl+N | 新建会话 |
| Ctrl+C | 中断当前生成 |
| Ctrl+Q | 退出 |
| F1     | 帮助 |

---

## 七、pyproject.toml

```toml
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
```

---

## 八、从 learn_agent 迁移

### 迁移对照表

| learn_agent 原始 | nb_agent 新路径 | 改动 |
|-----------------|----------------|------|
| `agent/core.py` | `core/agent.py` | 拆出 context.py, models.py, retry.py |
| `agent/mcp_client.py` | `mcp/client.py` | import 路径 |
| `agent/session.py` | `session/store.py` + `session/models.py` | sqlite3 → SQLModel |
| `agent/approval_rules.py` | `approval/engine.py` | import 路径 |
| `tools/base.py` | `tools/base.py` | 不变 |
| `tools/builtin.py` | `tools/builtin.py` | 不变 |
| `config_loader.py` | `config/loader.py` | 去掉硬编码路径 |
| `main.py` | `main.py` | CLI 参数重新设计 |
| `ui/app.py` | `tui/app.py` + `tui/widgets/*` | 拆分组件 |
| `ui/styles.tcss` | `tui/styles.tcss` | 不变 |

### 不迁移

| 删除 | 理由 |
|------|------|
| `rag/` 整个目录 | 已独立为 nb_agentic_rag (MCP) |
| `mcp_servers/` 整个目录 | MCP Server 各自独立 |
| `tools/extra_serena_tools.py` | Serena 通过 MCP 接入 |
| `data/` 目录 | 运行时生成 |

### 新增模块

| 模块 | 描述 | 工作量 |
|------|------|--------|
| `skills/manager.py` | SkillManager: 发现/加载/view_skill | 1 天 |
| `skills/builtin/*/SKILL.md` | 内置 Skill 文档 | 0.5 天 |
| `core/context.py` | 从 agent.py 拆出上下文管理 | 0.5 天 |
| `core/models.py` | 从 agent.py 拆出模型管理 | 0.5 天 |
| `core/retry.py` | 从 agent.py 拆出重试逻辑 | 0.5 天 |
| `tui/widgets/*` | 从 app.py 拆分组件 | 0.5 天 |

---

## 九、开发优先级

| 阶段 | 内容 | 估算 |
|------|------|------|
| P0 | 核心迁移: AgentCore + Tools + MCP + Session (SQLModel) + Config | 1.5 天 |
| P1 | TUI 迁移: app.py 拆分组件 + 适配新 AgentCore | 1 天 |
| P2 | Skills 系统: SkillManager + view_skill + 内置 SKILL.md | 1 天 |
| P3 | CLI 完善: `run` 模式 + `sessions` 子命令 | 0.5 天 |
| P4 | 测试 + README + PyPI | 1 天 |

**总计约 5 天。**

---

## 十、Agent 循环核心逻辑

```python
class AgentCore:
    def __init__(self, config: dict):
        self.tool_registry = ToolRegistry()      # 内置 tools
        self.mcp_manager = MCPManager(config)     # MCP tools
        self.skill_manager = SkillManager()       # Skills
        self.session_store = SessionStore(config)  # 会话存储
        self.approval_engine = ApprovalEngine(config)

    async def chat(self, session_id: str, user_input: str):
        """ReAct Agent 循环"""
        messages = self.session_store.get_messages(session_id)
        messages.append({"role": "user", "content": user_input})

        all_tools = self._merge_tools()  # 内置 + MCP + view_skill

        for round in range(self.max_rounds):
            response = await self._call_llm(messages, tools=all_tools)

            if response.tool_calls:
                for call in response.tool_calls:
                    # 审批检查
                    if self.approval_engine.needs_approval(call):
                        approved = await self._request_approval(call)
                        if not approved:
                            continue

                    result = await self._execute_tool(call)
                    messages.append(tool_result_message(call, result))
            else:
                # 无 tool_calls → Agent 完成
                break

        self.session_store.save_messages(session_id, messages)

    def _merge_tools(self) -> list[dict]:
        """合并三种来源的工具"""
        tools = []
        tools += self.tool_registry.get_schemas()     # 内置 tools
        tools += self.mcp_manager.get_schemas()        # MCP tools
        tools += [self.skill_manager.view_skill_schema]  # view_skill 工具
        return tools
```

---

## 十一、分发方式

```bash
# 方式 1: pip 安装后直接用
pip install nb_agent
nb_agent

# 方式 2: fork 后深度定制
git clone https://github.com/ydf0509/nb_agent
cd nb_agent
pip install -e ".[dev]"
```

### 定制化设计（大部分不需要 fork）

| 定制需求 | 方案 | 需要 fork? |
|---------|------|-----------|
| 换 LLM 模型/Provider | config.jsonc `provider` | 否 |
| 加自定义工具 | MCP Server（外部进程） | 否 |
| 改系统提示词 | config.jsonc `agent.system_prompt` | 否 |
| 加 Skill | 项目级 `.nb_agent/skills/` 或全局 `~/.nb_agent/skills/` | 否 |
| 改审批规则 | config.jsonc `approval` | 否 |
| 改 TUI 主题 | styles.tcss | 否（pip 安装后可覆盖） |
| 改 TUI 布局/交互 | 改 `tui/app.py` | **需要 fork** |
| 改 Agent 循环逻辑 | 改 `core/agent.py` | **需要 fork** |

---

## 十二、面试叙事

### 30 秒版

> "我开源了 nb_agent，一个手写的 ReAct Agent 框架。不依赖 LangChain，
> 纯 Python 实现 LLM ↔ Tool 循环。支持三种扩展方式：
> 内置 Tools、MCP 外部工具、Markdown Skills 指导手册。
> 赛博朋克风的 TUI 界面。"

### 深度版

> "我没用 LangChain，手写了整个 Agent 循环——LLM 调用、tool_calls 解析、
> 工具执行、结果回传。这让我深入理解了 Function Calling 的本质。
> 比如 DeepSeek 的 reasoning_content 需要特殊处理，框架做不到。
>
> 设计了三个正交的扩展维度：Tool（内置 Python 函数 + MCP 外部工具）、
> Skill（Markdown 指导手册，参考 Cursor Skills 的渐进式披露设计——
> 启动只读元数据，需要时按需加载）。
>
> 同时实现了 MCP 多 Server 管理（运行时启禁）、上下文裁剪、
> 指数退避重试、人工审批等生产级特性。
>
> Coding 能力通过 MCP 接入 Serena（语义级编程工具）获得，
> RAG 能力通过 MCP 接入 nb_agentic_rag 获得。
> Agent 本身是通用的，架构解耦。"
