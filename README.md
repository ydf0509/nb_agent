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

**遵循 [Agent Skills 开放规范](https://agentskills.io)**（Anthropic 创建，已被 26+ 平台采用：Claude、OpenAI Codex、Gemini CLI、GitHub Copilot、Cursor、VS Code 等）。

**渐进式披露（Progressive Disclosure）** — Agent Skills 规范的核心设计：
- **Discovery**：启动时 system prompt 只注入 Skills **清单摘要**（name + description），不浪费 token
- **Activation**：AI 判断需要某个 Skill 时，调用 `view_skill("code-review")` 工具加载完整指南
- **Execution**：AI 按照指南执行任务，按需加载 scripts/references 等资源

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

**frontmatter 字段说明（[agentskills.io 规范](https://agentskills.io/specification)）：**

| 字段 | 必须 | 说明 |
|------|------|------|
| `name` | 是 | kebab-case，max 64 chars，**必须与文件夹名一致** |
| `description` | 是 | max 1024 chars，包含 WHAT（做什么）+ WHEN（什么时候用）+ 触发关键词 |
| `license` | 否 | 许可证名称或引用（如 `Apache-2.0`） |
| `compatibility` | 否 | max 500 chars，环境要求（目标产品、系统依赖、网络访问等） |
| `metadata` | 否 | 任意键值对（如 `author`、`version`） |
| `allowed-tools` | 否 | 空格分隔的预授权工具（实验性，如 `Bash(git:*) Read`） |
| `paths` | 否 | glob 模式，作用域限定（nb_agent 扩展字段） |
| `disable-model-invocation` | 否 | 设为 `true` 时 AI 不会自动调用，只能手动触发（nb_agent 扩展字段） |

**自定义 Skill 示例**：

```bash
mkdir -p .nb_agent/skills/deploy-checklist   # 文件夹名 = deploy-checklist
```

```markdown
---
name: deploy-checklist                        # ⚠ 必须与文件夹名一致
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

## nb_log_config.py 配置

nb_agent 使用 [nb_log](https://github.com/ydf0509/nb_log) 作为日志库。TUI 模式下需要在项目根目录的 `nb_log_config.py` 中关闭以下 3 项配置，否则 **TUI 会黑屏**：

```python
PRINT_WRTIE_FILE_NAME = None   # 禁止 nb_log 劫持 sys.stdout 写文件
SYS_STD_FILE_NAME = None       # 禁止 nb_log 劫持 sys.stdout 写文件
AUTO_PATCH_PRINT = False       # 禁止 monkey patch print
```

> **原理**：Textual TUI 独占终端的 alternate screen buffer 进行渲染，`nb_log` 的 `SYS_STD_FILE_NAME` 和 `PRINT_WRTIE_FILE_NAME` 会 monkey patch `sys.stdout`，`AUTO_PATCH_PRINT` 会替换内置 `print`——这些都会破坏 Textual 的渲染通道导致黑屏。nb_agent 内部已处理了 MCP 子进程 stderr 和 logging handler 的重定向，用户只需确保这 3 项配置正确即可。

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
