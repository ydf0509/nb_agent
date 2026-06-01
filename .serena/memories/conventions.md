# nb_agent 代码规范与约定

## 命名规则

- **模块名**: 全小写，下划线分隔 (approval, tools, tui)
- **类名**: PascalCase (AgentCore, MCPManager, ApprovalEngine)
- **函数/方法**: snake_case (chat_stream, get_tools, _execute_with_approval)
- **dataclass**: PascalCase, 带字段类型注解 (ToolCallRecord, AgentResponse, ModelInfo)
- **私有方法**: 单下划线前缀 (_build_system_prompt)
- **回调属性**: on_xxx 命名 (on_tool_call, approval_callback)

## Pydantic 模型规范

- 每个 @tool 函数必须有且仅有一个 Pydantic BaseModel 参数
- 模型类名 = 功能名 + Params (GetCurrentTimeParams)
- Field(description=...) 必须写，作为 LLM 了解参数含义的依据
- docstring 作为工具描述，必须写

## @tool 装饰器规则

- `@tool`（无参数）：注册名 = 函数名
- `@tool(group="xxx")`：注册名 = `xxx__函数名`
- 内置工具 group 固定为 `nb_agent_builtin`
- 注册自动触发：import tools 即执行 _register_tool 写入 TOOL_REGISTRY

## ReAct 循环约定

- MAX_TOOL_ROUNDS = 30 轮上限
- LLM 返回 tool_calls → 执行 → 结果回传 → LLM 再次判断
- 非流式模式调用 chat()，流式模式调用 chat_stream()
- 工具执行通过 _execute_with_approval() 先过审批引擎
- 审批回调返回值决定是否继续

## MCP 约定

- 工具前缀: `mcp__{server}__{tool}`（3段式 split("__", 2)）
- is_mcp_tool() 判断: 以 `mcp__` 开头
- 每个 Server 的 enabled 默认 true
- SSE/HTTP 有独立 AsyncExitStack 管理生命周期，stdio 走统一的 _stdio_exit_stack

## 会话持久化

- SQLModel 3 张表: sessions, messages, agent_configs
- message 的 tool_calls 存 JSON 字符串 (tool_calls_json)
- SQLite，默认路径 ~/.nb_agent/sessions.db
- session_id 用 uuid4()[:8] 截取

## 异常处理

- 网络/超时错误重试: RETRYABLE_ERRORS + call_llm_with_retry (见 retry.py)
- 工具执行异常捕获: 返回字符串 "[错误]..."/"[超时]..."
- 审批拦截: 返回 "[已拦截]..."

## Skills 规范

- 严格遵循 agentskills.io 规范
- SKILL.md 包含 YAML frontmatter (name, description, paths, disable-model-invocation)
- 渐进式披露: Discovery → Activation(view_skill) → Execution
- 目录扫描: builtin → global → project (后者覆盖前者)

## 日志规范

- 5 个 logger 全部 is_add_stream_handler=False，仅写文件
- 日志文件: nb_agent_* (config, mcp, llm_call, llm_call_raw, httpx)
- TUI 模式下所有 terminal handler 重定向到 ~/.nb_agent/logs/tui_stdout.log
- nb_log_config.py 中三行关键配置不可缺（见 `mem:core` 不变约定）
