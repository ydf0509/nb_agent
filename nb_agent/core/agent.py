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

    DEFAULT_AGENT_ID = "__default__"

    def __init__(self, config: dict):
        self.config = config
        self._base_prompt = config.get("agent", {}).get("system_prompt", "你是一个智能助手。")
        self.current_agent_id = self.DEFAULT_AGENT_ID
        self.current_agent_name = "默认助手"
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
        self.system_prompt = self._build_system_prompt(self._base_prompt)
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
        self._seed_builtin_agents()
        self.session_id = str(uuid.uuid4())[:8]
        model_id = self.current_model.id if self.current_model else ""
        self.session_store.create_session(
            self.session_id, title="新会话", model_id=model_id,
            agent_id=self.current_agent_id,
        )

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
        self.session_store.create_session(
            self.session_id, title="新会话", model_id=model_id,
            agent_id=self.current_agent_id,
        )

    def get_session_list(self, limit: int = 50) -> list:
        return self.session_store.list_sessions(limit)

    def get_tools(self) -> list:
        builtin = []
        for name, t in self.tool_registry.items():
            group = t.get("group", "")
            func = t.get("function")
            module = getattr(func, "__module__", "") if func else ""
            is_builtin = module.startswith("nb_agent.tools.")
            source = "内置" if is_builtin else "第三方"
            builtin.append({
                "name": name,
                "func_name": t.get("func_name", name),
                "group": group,
                "description": t["schema"]["function"]["description"],
                "source": source,
                "disabled": group in self.disabled_tool_groups if group else False,
            })
        if self.skill_manager.get_manifest():
            builtin.append({
                "name": "view_skill",
                "func_name": "view_skill",
                "group": "nb_agent_builtin",
                "description": "查看 Skill 完整指南",
                "source": "Skills",
                "disabled": "nb_agent_builtin" in self.disabled_tool_groups,
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

    # ==================== Agent ====================

    BUILTIN_AGENTS = [
        {
            "id": "_news_search",
            "name": "新闻搜索",
            "system_prompt": (
                "你是一个新闻搜索助手。用户会给你一个新闻话题或关键词，你需要通过 web-search MCP "
                "工具帮用户搜索最新新闻并整理摘要。\n\n"
                "## web-search 搜索策略\n\n"
                "1. 使用 `searchWeb` 工具发起搜索，参数 `engines` 可选值：\n"
                "   bing, duckduckgo, sogou, startpage, brave, exa, csdn, juejin\n"
                "   每次搜索可组合使用多个引擎，如 [\"bing\",\"duckduckgo\",\"brave\"]\n"
                "   **注意：不要使用 baidu 引擎（免费用户不可用，搜不到内容）**\n\n"
                "2. 搜索完成后，从所有结果中筛选出质量最高、最相关的 **10 条**\n\n"
                "3. 使用 `fetchWebContent` 工具逐一抓取这 10 条的详情全文\n\n"
                "4. 最终整理为结构化的摘要呈现给用户，包括：\n"
                "   - 标题、来源、时间\n"
                "   - 核心内容摘要\n"
                "   - 原文链接\n\n"
                "## 输出格式\n\n"
                "按新闻的重要性和时效性排序，使用 Markdown 格式输出。"
            ),
        },
        {
            "id": "_code_review",
            "name": "代码审查",
            "system_prompt": (
                "你是一位资深的代码审查专家。用户会提供代码片段或文件，你需要：\n\n"
                "1. **正确性**：检查逻辑错误、边界条件、异常处理\n"
                "2. **安全性**：识别潜在安全漏洞（注入、XSS、敏感信息泄露等）\n"
                "3. **性能**：发现性能瓶颈和优化机会\n"
                "4. **可读性**：命名、注释、代码组织是否清晰\n"
                "5. **最佳实践**：是否符合语言/框架的惯用写法\n\n"
                "对每个问题给出具体位置、原因和修改建议。先总结关键问题，再逐项展开。"
            ),
        },
        {
            "id": "_translator",
            "name": "翻译助手",
            "system_prompt": (
                "你是一位专业翻译。根据输入文本自动检测源语言，翻译为目标语言。\n\n"
                "- 中文 → 英文，英文 → 中文（默认互译）\n"
                "- 用户可以指定目标语言\n"
                "- 保持原文的语气和风格\n"
                "- 专业术语给出注释\n"
                "- 如果是技术文档，保留代码块和格式不翻译"
            ),
        },
        {
            "id": "_writing",
            "name": "写作助手",
            "system_prompt": (
                "你是一位优秀的中文写作助手。帮助用户撰写、润色和优化各类文本。\n\n"
                "**能力范围**：\n"
                "- 文章写作：博客、技术文章、报告\n"
                "- 文案润色：改善表达、修正语病、提升可读性\n"
                "- 摘要提炼：从长文中提取核心观点\n"
                "- 大纲生成：根据主题生成结构化大纲\n\n"
                "**写作原则**：\n"
                "- 简洁有力，避免冗余\n"
                "- 逻辑清晰，层次分明\n"
                "- 用词准确，风格一致"
            ),
        },
    ]

    def _seed_builtin_agents(self):
        """首次启动时插入内置 Agent，已有则跳过"""
        existing = self.session_store.list_agents()
        existing_ids = {a["id"] for a in existing}
        for agent in self.BUILTIN_AGENTS:
            if agent["id"] not in existing_ids:
                self.session_store.create_agent(
                    agent["id"], agent["name"], agent["system_prompt"],
                    is_builtin=True,
                )

    def get_agents(self) -> list:
        """返回所有 Agent（含默认），当前使用的标记 is_current"""
        default = {
            "id": self.DEFAULT_AGENT_ID,
            "name": "默认助手",
            "system_prompt": self._base_prompt,
            "disabled_groups": [],
            "disabled_servers": [],
            "is_builtin": True,
        }
        saved = self.session_store.list_agents()
        result = [default] + saved
        return result

    def save_agent(self, name: str, system_prompt: str,
                   disabled_groups: list = None, disabled_servers: list = None) -> str:
        agent_id = str(uuid.uuid4())[:8]
        self.session_store.create_agent(
            agent_id, name, system_prompt,
            disabled_groups=disabled_groups, disabled_servers=disabled_servers,
        )
        return agent_id

    def update_agent(self, agent_id: str, name: str, system_prompt: str,
                     disabled_groups: list = None, disabled_servers: list = None):
        self.session_store.update_agent(
            agent_id, name, system_prompt,
            disabled_groups=disabled_groups, disabled_servers=disabled_servers,
        )
        if self.current_agent_id == agent_id:
            self.current_agent_name = name
            self.system_prompt = self._build_system_prompt(system_prompt)
            self.messages[0] = {"role": "system", "content": self.system_prompt}
            self.disabled_tool_groups = set(disabled_groups or [])
            self.mcp_manager.set_disabled_servers(disabled_servers or [])

    def delete_agent(self, agent_id: str) -> bool:
        if agent_id == self.DEFAULT_AGENT_ID:
            return False
        self.session_store.delete_agent(agent_id)
        if self.current_agent_id == agent_id:
            self.apply_agent(self.DEFAULT_AGENT_ID)
        return True

    def apply_agent(self, agent_id: str):
        """应用 Agent 配置：替换 system prompt + 工具开关，新建会话"""
        if agent_id == self.DEFAULT_AGENT_ID:
            agent_data = {
                "name": "默认助手",
                "system_prompt": self._base_prompt,
                "disabled_groups": [],
                "disabled_servers": [],
            }
        else:
            agent_data = self.session_store.get_agent(agent_id)
            if not agent_data:
                return

        self.current_agent_id = agent_id
        self.current_agent_name = agent_data["name"]
        self.system_prompt = self._build_system_prompt(agent_data["system_prompt"])
        self.disabled_tool_groups = set(agent_data.get("disabled_groups") or [])
        self.mcp_manager.set_disabled_servers(agent_data.get("disabled_servers") or [])

        self.messages = [{"role": "system", "content": self.system_prompt}]
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.last_turn_prompt = 0
        self.last_turn_completion = 0
        self.last_turn_tool_calls = 0
        self.session_id = str(uuid.uuid4())[:8]
        model_id = self.current_model.id if self.current_model else ""
        self.session_store.create_session(
            self.session_id, title="新会话", model_id=model_id,
            agent_id=agent_id,
        )
