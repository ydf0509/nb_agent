# AI 重大更新记录

## 2026-06-05: 工具调用并发执行（asyncio.gather）

**变更**：当 LLM 一次返回多个 tool_calls 时，从串行逐个执行改为并发执行，大幅降低多工具场景延迟。

**核心设计**：
- 新增 `_execute_tool_calls_batch(parsed_calls)` 方法
- 对不需要审批的工具使用 `asyncio.gather` 并发执行
- 对需要审批的工具保持串行执行（审批弹窗不能并发弹）
- 单个工具调用时直接走 `_execute_with_approval`，无额外开销
- 使用 `return_exceptions=True` 确保单个工具异常不会影响其他工具
- 执行完毕后按原始顺序组装 tool messages（OpenAI API 要求 id 匹配）

**改造范围**：
- `chat()` 非流式方法
- `chat_stream()` 流式方法（先公布所有工具名 → 并发执行 → 按序输出结果）

**涉及文件**：
- `core/agent.py` — `_execute_tool_calls_batch` + `chat()` + `chat_stream()`

## 2026-05-28: 列名正面语义统一 + 三值语义修复

**列名重命名（增强可读性）**：
- `allowed_groups_json` → `allowed_tool_groups_json`
- `allowed_servers_json` → `allowed_mcp_servers_json`
- `allowed_skills_json` → 不变
- 参数名同步：`allowed_groups` → `allowed_tool_groups`，`allowed_servers` → `allowed_mcp_servers`

## 2026-05-28: allowed_* 三值语义修复（None / [] / ["a","b"]）

**Bug**：用户取消勾选 Skills 后保存，重新打开又全部勾选。
**根因**：旧代码用 `[] = 全部允许` 和 `["a"] = 只允许 a`，无法表达"明确禁用全部"。
用户取消全部 → `selected=[]` → 存入 `'[]'` → 加载时解释为"全部允许" → 全勾选。

**修复**：引入 `None` 作为"无限制（默认全部允许）"，`[]` 表示"明确选择零个"：
- `None` → DB 存 `'null'`，加载后 `allowed is None` → 全部允许
- `[]` → DB 存 `'[]'`，加载后 `allowed == set()` → 全部禁用
- `["a","b"]` → DB 存 `'["a","b"]'`，加载后 `allowed == {"a","b"}` → 只允许 a 和 b

**涉及文件**：
- `session/models.py` — 默认值从 `"[]"` 改为 `"null"`
- `session/store.py` — `json.dumps(None)` 产出 `'null'`，`_deserialize_agent` 处理 null
- `core/agent.py` — `self.allowed_tool_groups/skills` 初始化为 `None`，判断改为 `is None`
- `mcp/client.py` — `_allowed_servers` 初始化为 `None`，所有 `not x` 改为 `x is None`
- `skills/manager.py` — `get_manifest(allowed_skills=None)` 用 `is None`
- `tui/widgets/screens.py` — `_build_*_list` 和 `AgentContentScreen` 用 `is None`
- `tui/app.py` — `_on_agent_saved` 用 `.get()` 不设默认值（允许 None 穿透）

## 2026-05-28: disabled_* → allowed_* 正面语义重构 + 删除内置 Agent

**变更 1：语义翻转**：
- 全局重命名 `disabled_groups/servers/skills` → `allowed_groups/servers/skills`
- `allowed_* = []` 表示"无限制，全部允许"（默认值）
- `allowed_* = ["search", "note"]` 表示"只允许这些"
- 检查逻辑：`if self.allowed_tool_groups and group not in self.allowed_tool_groups: skip`
- DB 列：`allowed_groups_json` / `allowed_servers_json` / `allowed_skills_json`
- `_migrate_schema()` 自动补列，旧 `disabled_*_json` 列保留但不再使用

**变更 2：删除所有内置 Agent**：
- 移除 `BUILTIN_AGENTS` 常量（新闻搜索、代码审查、翻译助手、写作助手）
- 移除 `_seed_builtin_agents()` 方法
- 框架只保留 `__default__` 默认助手
- 保留 `is_builtin` 字段用于未来扩展

**涉及文件**：
- `session/models.py` — 三个字段重命名
- `session/store.py` — CRUD + `_migrate_schema()` + `_deserialize_agent()`
- `core/agent.py` — `allowed_tool_groups`/`allowed_skills` + 全套方法 + 删除内置 Agent
- `mcp/client.py` — `_allowed_servers` + `is_server_enabled()` + `set_allowed_servers()`
- `skills/manager.py` — `get_manifest(allowed_skills=...)`
- `tui/widgets/screens.py` — AgentEditScreen + AgentContentScreen
- `tui/app.py` — `_on_agent_saved` 回调

## 2026-05-28: Agent 可控制 Skills 启用/禁用

**变更**：Agent 新增 Skills 勾选列表，可以控制哪些 Skill 注入到 AI 上下文。

**数据模型**：
- `AgentConfig` 新增 `disabled_skills_json` 字段
- `SessionStore` 自动迁移旧数据库（ALTER TABLE 补列）

**核心逻辑**：
- `AgentCore` 新增 `disabled_skills: set`，传递给 `SkillManager.get_manifest()`
- `SkillManager.get_manifest(disabled_skills=...)` 过滤被禁用的 Skill
- 被禁用的 Skill 不出现在 system prompt 的 Skills 清单中，AI 完全看不到

**UI**：
- `AgentEditScreen` 新增 Skills 勾选列表（✓ 启用 = 注入到 AI 上下文）
- 支持"全部启用"/"全部禁用"按钮
- `SkillListScreen (F2)` 新增"应用"按钮，点击后插入 `@skill:name` 到输入框

**设计说明**：
- agentskills.io 标准没有"对 AI 隐藏"字段，`disable-model-invocation` 只是"不自动调用"
- Agent 的 disabled_skills 是 nb_agent 平台层概念，效果等同于文件夹不存在

**涉及文件**：
- `session/models.py` — `disabled_skills_json`
- `session/store.py` — `_migrate_schema()` + CRUD 更新
- `core/agent.py` — `disabled_skills` + `save/update/apply/get`
- `skills/manager.py` — `get_manifest(disabled_skills=...)`
- `tui/widgets/screens.py` — `AgentEditScreen._build_skills_list()` + `SkillListScreen` 应用按钮
- `tui/app.py` — `_on_agent_saved` 传 `disabled_skills` + `_on_skill_selected` 处理 `__apply__`

## 2026-05-28: TUI 黑屏修复 — MCP 子进程 stderr + nb_log 输出重定向

**问题根因**：TUI 启动后一片漆黑，两个原因：
1. **MCP 子进程 stderr 泄漏**：MCP SDK 的 `stdio_client(server_params)` 默认把子进程 stderr 输出到 `sys.stderr`（终端），
   直接破坏 Textual 的 alternate screen buffer 渲染
2. **nb_log 输出泄漏**：nb_log 的 StreamHandler、startup logo、monkey_print 等输出到终端

**修复方案（三层拦截）**：
1. `nb_log_config.py`：关闭 `AUTO_PATCH_PRINT`、`SHOW_NB_LOG_LOGO`、`SHOW_PYCHARM_COLOR_SETINGS`、
   `SHOW_IMPORT_NB_LOG_CONFIG_PATH`；`PRINT_WRTIE_FILE_NAME = None`、`SYS_STD_FILE_NAME = None`
2. `nb_agent/mcp/client.py`：`MCPManager` 新增 `errlog` 属性，`_connect_stdio()` 传 `errlog` 给 `stdio_client()`
3. `nb_agent/tui/app.py`：
   - `__init__` 打开 `~/.nb_agent/logs/tui_stdout.log` 并设置给 `mcp_manager.errlog`
   - `on_mount()` 调用 `_redirect_all_handlers()`：遍历所有 logging handler，把指向终端的 stream 重定向到日志文件
   - **不动 `sys.stdout/stderr`**（Textual 需要它们来渲染），只在 handler 层面和 nb_log 内部引用层面拦截

**关键原则**：绝不直接修改 `sys.stdout`，Textual 必须完全控制终端。

**涉及文件**：
- `nb_log_config.py`
- `nb_agent/mcp/client.py` — `errlog` 属性 + `stdio_client(errlog=...)` 调用
- `nb_agent/tui/app.py` — `_redirect_all_handlers()` + `mcp_manager.errlog` 赋值

## 2026-05-28: nb_log 日志系统集成 + LLM 交互日志

**变更**：引入 `nb_log` 替换标准 `logging`，并添加 LLM 请求/响应日志。

**nb_log 集成**：
- `nb_agent/utils/loggers.py`：统一定义所有 logger（`logger_httpx`、`logger_config`、`logger_mcp`、`logger_llm`）
- `nb_agent/mcp/client.py`：`import logging` → `from nb_agent.utils.loggers import logger_mcp`
- `nb_agent/config/loader.py`：临时 `logging.warning()` → `logger_config.warning()`
- `pyproject.toml`：新增依赖 `nb_log>=9.0.0`

**LLM 交互日志**：
- `nb_agent/core/retry.py`：`call_llm_with_retry()` 每次 LLM 调用记录请求体摘要、响应摘要、耗时到 `nb_agent_llm_calls.log`
- 日志内容：model、message_count、tool_names、finish_reason、content_preview、usage、重试/失败信息

**TUI 状态栏增强**：
- `core/agent.py`：新增 `last_turn_rounds` 计数器（记录本次提问的 API 交互轮数）
- `tui/app.py`：状态栏新增 "交互N轮"（当 rounds > 1 时显示）

## 2026-05-28: nb_agent_bfzs 添加 Redis MCP + 自定义审批规则

**变更**：
- `mcp_servers/redis_tools_server.py`：从 ai_proj 复制，7 个 Redis 工具
- `DANGEROUS_COMMANDS` → `FORBIDDEN_COMMANDS`（语义更准确：禁止 vs 审批）
- `approval_rules.py`（新建）：演示 nb_agent 的 ApprovalEngine 可插拔规则
  - `rule_redis_write`：Redis 写命令弹窗确认，只读命令放行
  - `rule_dangerous_tools`：黑名单工具始终确认
  - `rule_note_delete`：删除笔记需要确认
- `main.py`：注册自定义审批规则到 `app.agent.approval_engine`
- `config.jsonc`：新增 redis-tools MCP 配置

**nb_agent core 精简**：
- `approval/engine.py`：移除 Redis 相关硬编码规则，只保留纯框架 ApprovalEngine 类

**工具名格式规则**：
- `@tool(group="note") def delete_note` → `note__delete_note`
- `@tool() def get_time` → `get_time`
- MCP 工具 → `mcp__{config key}__{函数名}`

---

## 2026-05-28: 项目拆分 — nb_agent core + nb_agent_bfzs demo

**变更**：将 nb_agent 拆分为纯框架和独立演示项目。

**nb_agent core 精简**：
- 移除 `calculate` 内置工具，只保留 `get_current_time` 和 `view_skill`（框架必需）
- 移除 `nb_agent/skills/builtin/` 下的 3 个内置 Skill（code-review、refactor、explain-code）
- `__init__.py` 导出 `load_config` 和 `AgentApp`，用户可直接 `from nb_agent import load_config, AgentApp`
- `examples/demo2/` 精简为最小示例

**nb_agent_bfzs 演示项目** (`D:/codes/nb_agent_bfzs/`)：
- `main.py`：6 行核心代码即可启动完整 Agent TUI
- `tools/`：笔记工具(5个) + 项目统计工具(2个)
- `mcp_servers/`：书签管理 MCP Server
- `.nb_agent/skills/`：6 个 Skill（daily-report、meeting-notes、git-changelog、code-review、refactor、explain-code）
- `config.jsonc`：完整配置模板（DeepSeek + LiteLLM 可选）

**其他修改**：
- AgentEditScreen 勾选符号 `X` → `✓`（通过 `ToggleButton.BUTTON_INNER`）
- 工具组/MCP 列表文案从"取消勾选=禁用"改为正面表述"✓ 启用"
- 添加"全部启用"/"全部禁用"按钮
- 内置 Skill 的 `paths` 字段已移除（非 agentskills.io 规范）
- README/TUI 补全 agentskills.io 规范所有 Front Matter 字段
- `@modelcontextprotocol/server-filesystem` 配置修复：必须加路径参数

---

## 2026-05-28: Agent 智能体功能（取代旧的 Preset/提示词）

**功能**：Agent 是 nb_agent 的核心概念，每个 Agent 绑定一套 system prompt + 工具分组开关 + MCP 服务器开关。应用 Agent 会创建新会话，会话绑定 agent_id。

**数据模型**：
- `AgentConfig`（SQLModel table），字段：id / name / system_prompt / disabled_groups_json / disabled_servers_json / is_builtin / created_at / updated_at
- `ChatSession` 增加 `agent_id` 字段（默认 `__default__`）
- 旧的 `PromptPreset` 已完全移除

**后端接口**：
- `SessionStore`：`create_agent()` / `list_agents()` / `get_agent()` / `update_agent()` / `delete_agent()`；`create_session()` / `get_session()` 支持 `agent_id`
- `AgentCore`：
  - `get_agents()` — 返回所有 Agent（含默认 `__default__`），第一项始终是默认
  - `save_agent()` / `update_agent()` / `delete_agent()` — CRUD
  - `apply_agent(agent_id)` — 核心方法：设置 system_prompt + disabled_tool_groups + mcp disabled_servers + 清空 token + 新建 session
  - `BUILTIN_AGENTS` — 4 个内置 Agent（新闻搜索、代码审查、翻译助手、写作助手），is_builtin=True，不可编辑但可复制
  - `_seed_builtin_agents()` — 首次启动时写入

**TUI**：
- F4 快捷键 → `AgentSelectScreen`（Agent 列表，按钮：查看详情/编辑/应用/复制/新建/删除）
- `AgentContentScreen` — 查看 Agent 完整信息
- `AgentEditScreen` — 新建/编辑 Agent，包含名称、system prompt、`SelectionList` 选择工具分组和 MCP 服务器
- 内置 Agent 不可编辑，只能复制
- Ctrl+P 命令面板"新建 Agent"
- F1 帮助文本：F4 描述更新为"Agent 管理（提示词+工具配置）"

**MCP**：
- `MCPManager.set_disabled_servers(names)` — 允许 Agent 批量控制 MCP 服务器开关

**涉及文件**：
- `nb_agent/session/models.py` — `AgentConfig` 类 + `ChatSession.agent_id`
- `nb_agent/session/store.py` — agent CRUD + session 绑定
- `nb_agent/core/agent.py` — `BUILTIN_AGENTS` / `apply_agent()` / agent 全套方法
- `nb_agent/mcp/client.py` — `set_disabled_servers()`
- `nb_agent/tui/widgets/screens.py` — `AgentSelectScreen` / `AgentContentScreen` / `AgentEditScreen`
- `nb_agent/tui/widgets/__init__.py` — 导出新弹窗
- `nb_agent/tui/widgets/commands.py` — 命令面板"新建 Agent"
- `nb_agent/tui/app.py` — F4 绑定 + agent 相关回调方法
- `nb_agent/tui/styles.tcss` — Agent 弹窗样式
- `examples/demo2/README.md` — F4 快捷键描述更新
- `tests/ai_codes/regression_testing/test_preset.py` — 22 个回归测试

---

## 2026-05-28: 工具分组管理内联到右侧面板 + 移除 F3 弹窗

**改动**：
- 在右侧 ToolPanel 中，MCP Server 区块和工具列表之间新增了"工具分组"区块
- 使用 OptionList 实现，用户可直接点击分组来切换启用/禁用（与 MCP 切换交互一致）
- MCP 类型的分组不在此显示（已由 MCP Server 区块管理）
- 移除了 F3 快捷键和 `ToolGroupToggleScreen` 弹窗（功能已内联到面板）
- 清理了 styles.tcss 中 ToolGroupToggleScreen 相关样式，新增 section-groups-list 样式
- 更新了 HelpScreen 快捷键列表和 demo2 README 快捷键表

**右侧面板布局顺序**：
1. Token 用量
2. 模型列表（点击切换）
3. MCP Server（点击切换）
4. **工具分组（点击切换）** ← 新增
5. 工具列表（点击查看详情）

**涉及文件**：
- `nb_agent/tui/widgets/tool_panel.py` - compose() 新增 section-groups-title/list
- `nb_agent/tui/widgets/screens.py` - 移除 ToolGroupToggleScreen 类，更新 HelpScreen
- `nb_agent/tui/widgets/__init__.py` - 移除 ToolGroupToggleScreen 导出
- `nb_agent/tui/app.py` - 移除 F3 binding 和相关方法/import
- `nb_agent/tui/styles.tcss` - 移除弹窗样式，新增面板分组样式
- `examples/demo2/README.md` - 更新快捷键表

---

## 2026-05-28: 修复工具详情/面板的来源标识和颜色区分

**问题**：
- `get_tools()` 把所有 `@tool` 注册的工具都标记为"内置"，无法区分真正内置工具和第三方工具
- ToolDetailScreen 弹窗、右侧 ToolPanel、@ 补全弹窗、工具分组管理弹窗中，第三方工具错误显示为内置绿色
- 已禁用的工具组显示灰色，不够醒目

**修改**：
1. `agent.py` - `get_tools()`: 通过 `func.__module__` 判断工具来源，`nb_agent.tools.*` 模块的标记为"内置"，其他标记为"第三方"
2. 统一颜色方案（涉及 `screens.py` 的 ToolDetailScreen/MentionSelectScreen/ToolGroupToggleScreen，以及 `tool_panel.py`）：
   - 内置工具：绿色 `●` (#6bcb77)
   - 第三方 @tool 工具：蓝色 `●` (#4d96ff)
   - MCP 工具：紫色 `◆` (#b39ddb)
   - Skills：特殊标记（已有）
   - 已禁用工具/分组：黄色 `○` (#ffd93d)

**涉及文件**：
- `nb_agent/core/agent.py` - get_tools()
- `nb_agent/tui/widgets/screens.py` - ToolDetailScreen, MentionSelectScreen, ToolGroupToggleScreen
- `nb_agent/tui/widgets/tool_panel.py` - update_content()
