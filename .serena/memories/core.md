# nb_agent — 手写 ReAct Agent 框架 + 赛博朋克 TUI

## 项目定位

纯 Python 实现的 LLM ↔ Tool 循环框架，零 LangChain 依赖。
pip install nb_agent 即可使用，支持三种正交扩展方式。

## 项目结构（含测试/示例）

```
nb_agent/
├── approval/        — ApprovalEngine, 可插拔工具审批规则引擎
├── config/          — config/loader.py, JSONC 配置 + {env:VAR} 环境变量替换
├── core/            — ReAct 核心循环
│   ├── agent.py     — AgentCore, 非流式/流式 chat, MCP/Skills/工具管理
│   ├── context.py   — 上下文裁剪 (trim_context)
│   ├── models.py    — ToolCallRecord, AgentResponse, ModelInfo dataclasses
│   └── retry.py     — 指数退避重试
├── mcp/             — MCPManager, 多 Server 管理 (stdio/SSE/HTTP)
├── session/         — SQLModel 持久化 (ChatSession, Message, AgentConfig)
├── skills/          — SkillManager, 渐进式披露 SKILL.md (agentskills.io 规范)
│   └── builtin/     — 内置 Skills (当前为空，无内置 skill)
├── tools/           — @tool 装饰器 + TOOL_REGISTRY + 内置工具
├── tui/             — Textual 赛博朋克 TUI
│   ├── app.py       — AgentApp 主应用
│   ├── styles.tcss  — CSS 样式
│   └── widgets/     — ChatInput, ToolPanel, 各种 ModalScreen
└── utils/           — nb_log 日志配置 (5 个 logger, 均 is_add_stream_handler=False)

tests/               — 回归测试 + 示例项目
├── ai_codes/        — 自动生成的修复/重建脚本
├── my_tests/        — 测试笔记
├── deletes/examples/demo2/ — 完整示例项目（带工具/MCP/Skills）
└── test_*.py        — pytest 测试 (config, session, skills, tools)
```

```
nb_agent/
├── approval/        — ApprovalEngine, 可插拔工具审批规则引擎
├── config/          — config/loader.py, JSONC 配置 + {env:VAR} 环境变量替换
├── core/            — ReAct 核心循环
│   ├── agent.py     — AgentCore, 非流式/流式 chat, MCP/Skills/工具管理
│   ├── context.py   — 上下文裁剪 (trim_context)
│   ├── models.py    — ToolCallRecord, AgentResponse, ModelInfo dataclasses
│   └── retry.py     — 指数退避重试
├── mcp/             — MCPManager, 多 Server 管理 (stdio/SSE/HTTP)
├── session/         — SQLModel 持久化 (ChatSession, Message, AgentConfig)
├── skills/          — SkillManager, 渐进式披露 SKILL.md (agentskills.io 规范)
├── tools/           — @tool 装饰器 + TOOL_REGISTRY + 内置工具
├── tui/             — Textual 赛博朋克 TUI
│   ├── app.py       — AgentApp 主应用
│   ├── styles.tcss  — CSS 样式
│   └── widgets/     — ChatInput, ToolPanel, 各种 ModalScreen
└── utils/           — nb_log 日志配置 (5 个 logger, 均 is_add_stream_handler=False)
```

## 核心架构不变约定

- **AgentCore** 是唯一中枢，所有功能入口（chat/stream/MCP/切换模型/Agent管理）
- **TOOL_REGISTRY** 全局 dict，tools/__init__.py import 触发注册
- **MCP 工具命名**: `mcp__{server}__{tool}` 前缀防冲突
- **Skills 目录扫描优先级**: 内置 → ~/.nb_agent/skills → ~/.agents/skills → .nb_agent/skills → .agents/skills（后者覆盖前者）
- **配置优先级**: CLI > 环境变量 > ./config.jsonc > ~/.nb_agent/config.jsonc > 默认值
- **Agent 三值语义**: allowed_tool_groups / allowed_mcp_servers / allowed_skills = None 表示全部允许, [] 全部禁用, ['a','b'] 只允许选中
- **TUI 运行的前提**: nb_log_config.py 必须设 PRINT_WRTIE_FILE_NAME=None, SYS_STD_FILE_NAME=None, AUTO_PATCH_PRINT=False

## 引用

- 技术栈: `mem:tech_stack`
- 代码规范: `mem:conventions`
- 常用命令: `mem:suggested_commands`
- 任务完成检查: `mem:task_completion`
