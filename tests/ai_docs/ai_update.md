# AI 重大更新记录

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
