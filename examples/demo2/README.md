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
| `Tab` | 切换模型 |
| `F1` | 帮助 |
| `F2` | Skills 列表 |
| `F4` | Agent 管理（提示词+工具配置） |
| `Ctrl+P` | 命令面板 |
| `Ctrl+Q` | 退出 |

右侧面板可直接点击切换模型、MCP Server、工具分组。

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
