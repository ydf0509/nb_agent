# nb_agent 技术栈

## 语言 & 解释器

- **Python >= 3.11**（项目 requires-python=">=3.11"）
- 开发解释器: `D:\ProgramData\Miniconda3\envs\py312\python.exe` (Python 3.12)
- AGENTS.md 指定必须使用 python3.12 运行

## 核心依赖

| 包 | 用途 | 版本约束 |
|---|---|---|
| `textual` | TUI 框架 (RichLog, App, CSS) | >=0.50.0 |
| `rich` | 终端富文本渲染 (Markdown, Panel, Text) | >=13.0.0 |
| `json5` | JSONC 配置解析 (支持注释) | >=0.9.0 |
| `openai` | OpenAI 兼容 API (AsyncOpenAI) | >=1.0.0 |
| `httpx` | HTTP 客户端 (openai 的底层) | >=0.24.0 |
| `pydantic` | @tool 参数校验 + schema 生成 | >=2.0.0 |
| `mcp` | MCP 客户端 (stdio/SSE/HTTP) | >=1.0.0 |
| `sqlmodel` | SQLite ORM (会话/消息/Agent 持久化) | >=0.0.16 |
| `nb_log` | 日志框架 (配置见 nb_log_config.py) | 无版本约束 |
| `python-dotenv` | .env 文件加载 | >=1.0.0 |
| `pyyaml` | Skills SKILL.md frontmatter 解析 | >=6.0 |

## 构建 & 打包

- `hatchling` (pyproject.toml 中 `[build-system]`)
- CLI 入口: `nb_agent = "nb_agent.main:main"`

## 传输协议

- MCP 支持 4 种传输: `local`(stdio, 默认), `sse`, `streamableHttp`, `http`(别名)
- LLM API: OpenAI 兼容格式，按 provider 分组配置
