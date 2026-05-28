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
import time
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
from nb_agent.utils.loggers import logger_llm_call, logger_llm_call_raw


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
        self.last_turn_rounds = 0

        self.tool_registry: Dict[str, dict] = dict(TOOL_REGISTRY)

        project_root = config.get("_project_root", "")
        self.skill_manager = SkillManager(
            project_root=__import__("pathlib").Path(project_root) if project_root else None
        )
        self.skill_manager.discover()
        self.allowed_tool_groups: set = None
        self.allowed_skills: set = None
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

        self.mcp_manager = MCPManager()

        db_path = config.get("session", {}).get("db_path", "")
        self.session_store = SessionStore(db_path)
        self.session_id = str(uuid.uuid4())[:8]
        model_id = self.current_model.id if self.current_model else ""
        self.session_store.create_session(
            self.session_id, title="新会话", model_id=model_id,
            agent_id=self.current_agent_id,
        )

    def _build_system_prompt(self, base_prompt: str) -> str:
        """在用户 system_prompt 末尾追加当前日期 + Skills 清单"""
        import datetime as _dt
        now = _dt.datetime.now()
        weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        date_str = f"{now.strftime('%Y-%m-%d')} {weekdays[now.weekday()]}"
        parts = [base_prompt, "", f"当前日期: {date_str}"]

        manifest = self.skill_manager.get_manifest(allowed_skills=self.allowed_skills)
        if manifest:
            parts.append("")
            parts.append("## 可用 Skills")
            parts.append("以下是你可以使用的技能指南。当任务匹配某个 Skill 时，先调用 `view_skill` 工具获取完整指南再执行。")
            parts.append("")
            for s in manifest:
                parts.append(f"- **{s['name']}**: {s['description']}")
            parts.append("")
            parts.append("调用方式: `view_skill(skill_name=\"<name>\")` 获取完整指南内容。")
        return "\n".join(parts)

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
        """合并内置 tools + MCP tools + Skills view_skill，按 allowed 过滤"""
        tools = []
        for t in self.tool_registry.values():
            group = t.get("group", "")
            if group and self.allowed_tool_groups is not None and group not in self.allowed_tool_groups:
                continue
            tools.append(t["schema"])
        tools.extend(self.mcp_manager.get_all_tools_openai_format())
        if self.skill_manager.get_manifest(allowed_skills=self.allowed_skills):
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
        self.last_turn_rounds = 0

        for round_idx in range(self.MAX_TOOL_ROUNDS):
            self.last_turn_rounds = round_idx + 1
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
        self.last_turn_rounds = 0

        for round_idx in range(self.MAX_TOOL_ROUNDS):
            self.last_turn_rounds = round_idx + 1
            try:
                kwargs = {
                    "model": self.current_model.id,
                    "messages": self._clean_messages_for_api(),
                    "stream": True,
                }
                kwargs["stream_options"] = {"include_usage": True}
                if openai_tools:
                    kwargs["tools"] = openai_tools

                stream_resp = await call_llm_with_retry(client, **kwargs)
                stream_t0 = time.monotonic()

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

                stream_elapsed = time.monotonic() - stream_t0
                stream_summary = {
                    "content_length": len(full_content),
                    "reasoning_length": len(full_reasoning),
                    "has_tool_calls": has_tool_calls,
                    "tool_calls": [
                        {"name": tc["name"], "args": tc["arguments"][:200]}
                        for tc in tool_calls_map.values()
                    ] if has_tool_calls else [],
                    "usage": {"prompt": self.last_turn_prompt, "completion": self.last_turn_completion},
                }
                logger_llm_call.info(
                    f"[LLM流式完成] round={round_idx + 1} elapsed={stream_elapsed:.2f}s | "
                    f"{json.dumps(stream_summary, ensure_ascii=False, default=str)}\n\n"
                )
                raw_resp = {
                    "content": full_content,
                    "reasoning_content": full_reasoning,
                    "tool_calls": [tool_calls_map[k] for k in sorted(tool_calls_map.keys())] if has_tool_calls else [],
                    "usage": {"prompt": self.last_turn_prompt, "completion": self.last_turn_completion},
                }
                logger_llm_call_raw.info(
                    f"[LLM流式完成-RAW] round={round_idx + 1} elapsed={stream_elapsed:.2f}s\n"
                    f"{json.dumps(raw_resp, ensure_ascii=False, default=str, indent=2)}\n\n"
                )

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
                "disabled": (self.allowed_tool_groups is not None and group not in self.allowed_tool_groups) if group else False,
            })
        if self.skill_manager.get_manifest(allowed_skills=self.allowed_skills):
            builtin.append({
                "name": "view_skill",
                "func_name": "view_skill",
                "group": "nb_agent_builtin",
                "description": "查看 Skill 完整指南",
                "source": "Skills",
                "disabled": self.allowed_tool_groups is not None and "nb_agent_builtin" not in self.allowed_tool_groups,
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
                "disabled": not self.mcp_manager.is_server_enabled(server),
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
        if self.allowed_tool_groups is None:
            all_groups = {t.get("group", "") for t in self.tool_registry.values() if t.get("group")}
            self.allowed_tool_groups = all_groups - {group}
            return False
        if group in self.allowed_tool_groups:
            self.allowed_tool_groups.discard(group)
            return False
        self.allowed_tool_groups.add(group)
        return True

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
            "last_rounds": self.last_turn_rounds,
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

    def get_agents(self) -> list:
        """返回所有 Agent（含默认），当前使用的标记 is_current"""
        default = {
            "id": self.DEFAULT_AGENT_ID,
            "name": "默认助手",
            "system_prompt": self._base_prompt,
            "allowed_tool_groups": None,
            "allowed_mcp_servers": None,
            "allowed_skills": None,
            "is_builtin": True,
        }
        saved = self.session_store.list_agents()
        result = [default] + saved
        return result

    def save_agent(self, name: str, system_prompt: str,
                   allowed_tool_groups: list = None,
                   allowed_mcp_servers: list = None,
                   allowed_skills: list = None) -> str:
        agent_id = str(uuid.uuid4())[:8]
        self.session_store.create_agent(
            agent_id, name, system_prompt,
            allowed_tool_groups=allowed_tool_groups,
            allowed_mcp_servers=allowed_mcp_servers,
            allowed_skills=allowed_skills,
        )
        return agent_id

    def update_agent(self, agent_id: str, name: str, system_prompt: str,
                     allowed_tool_groups: list = None,
                     allowed_mcp_servers: list = None,
                     allowed_skills: list = None):
        self.session_store.update_agent(
            agent_id, name, system_prompt,
            allowed_tool_groups=allowed_tool_groups,
            allowed_mcp_servers=allowed_mcp_servers,
            allowed_skills=allowed_skills,
        )
        if self.current_agent_id == agent_id:
            self.current_agent_name = name
            self.allowed_skills = set(allowed_skills) if allowed_skills is not None else None
            self.system_prompt = self._build_system_prompt(system_prompt)
            self.messages[0] = {"role": "system", "content": self.system_prompt}
            self.allowed_tool_groups = set(allowed_tool_groups) if allowed_tool_groups is not None else None
            self.mcp_manager.set_allowed_servers(allowed_mcp_servers)

    def delete_agent(self, agent_id: str) -> bool:
        if agent_id == self.DEFAULT_AGENT_ID:
            return False
        self.session_store.delete_agent(agent_id)
        if self.current_agent_id == agent_id:
            self.apply_agent(self.DEFAULT_AGENT_ID)
        return True

    def apply_agent(self, agent_id: str):
        """应用 Agent 配置：替换 system prompt + 工具/MCP/Skills 开关，新建会话"""
        if agent_id == self.DEFAULT_AGENT_ID:
            agent_data = {
                "name": "默认助手",
                "system_prompt": self._base_prompt,
                "allowed_tool_groups": None,
                "allowed_mcp_servers": None,
                "allowed_skills": None,
            }
        else:
            agent_data = self.session_store.get_agent(agent_id)
            if not agent_data:
                return

        self.current_agent_id = agent_id
        self.current_agent_name = agent_data["name"]
        raw_skills = agent_data.get("allowed_skills")
        self.allowed_skills = set(raw_skills) if raw_skills is not None else None
        self.system_prompt = self._build_system_prompt(agent_data["system_prompt"])
        raw_groups = agent_data.get("allowed_tool_groups")
        self.allowed_tool_groups = set(raw_groups) if raw_groups is not None else None
        self.mcp_manager.set_allowed_servers(agent_data.get("allowed_mcp_servers"))

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
