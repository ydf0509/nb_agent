"""
TUI 界面 —— 用 Textual 框架构建

布局:
┌─────────────────────────────────────────────────┐
│  nb_agent | deepseek-v4-flash | Tokens: 0       │  ← Header
├──────────────────────────────┬──────────────────-┤
│                              │  已注册工具:      │
│  对话区域（滚动）             │  - get_time      │  ← Main
│                              │  - calculate     │
│  user: 你好                  │                  │
│  model: [流式输出中...]       │  MCP: 未连接      │
│                              │                  │
├──────────────────────────────┴──────────────────-┤
│  > 输入消息...                          [发送]   │  ← Input
│  (Enter=发送, Shift+Enter=换行)                  │
├─────────────────────────────────────────────────┤
│  Tab=模型 | Ctrl+Q=退出 | Ctrl+L=清屏            │  ← Footer
└─────────────────────────────────────────────────┘
"""

import asyncio
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Footer, Header, RichLog, Static
from textual.binding import Binding
from textual.screen import ModalScreen
from rich.text import Text
from rich.markdown import Markdown as RichMarkdown
from rich.panel import Panel

from nb_agent.core import AgentCore
from .widgets import (
    ChatInput,
    ToolPanel,
    ModelSelectScreen,
    HelpScreen,
    SessionSelectScreen,
    ToolDetailScreen,
    RoundsInputScreen,
    ToolApprovalScreen,
    SkillListScreen,
    SkillContentScreen,
    MentionSelectScreen,
    AgentSelectScreen,
    AgentEditScreen,
    AgentCommands,
)
from .widgets.tool_panel import _fmt_tokens


_SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
_SPINNER_BIG = ["◐", "◓", "◑", "◒"]
_MARQUEE_BASE = "  ◐  AI 正在回答中，请稍候...  按 Ctrl+K 停止  ✦  "
_RAINBOW_COLORS = [
    "#ff0080", "#ff2060", "#ff4040", "#ff6020",
    "#ff8000", "#ffb000", "#ffff00", "#80ff00",
    "#00ff80", "#00ffff", "#0080ff", "#4040ff",
    "#8000ff", "#c000ff", "#ff00ff", "#ff0080",
]


class AgentApp(App):
    """nb_agent TUI 主应用"""

    TITLE = "nb_agent"
    CSS_PATH = "styles.tcss"

    COMMANDS = App.COMMANDS | {AgentCommands}

    BINDINGS = [
        Binding("ctrl+j", "send_msg", "发送", show=True, priority=True),
        Binding("ctrl+k", "stop_ai", "终止", show=True, priority=True),
        Binding("ctrl+up", "edit_last", "编辑上轮", show=True, priority=True),
        Binding("tab", "select_model", "模型", show=True, priority=True),
        Binding("ctrl+n", "new_session", "新建", show=True, priority=True),
        Binding("ctrl+r", "resume_session", "恢复", show=True, priority=True),
        Binding("ctrl+e", "toggle_input", "展开", show=True, priority=True),
        Binding("ctrl+l", "clear_chat", "清屏", show=True),
        Binding("f1", "show_help", "帮助", show=True),
        Binding("f2", "show_skills", "Skills", show=True),
        Binding("f4", "show_agents", "Agents", show=True),
        Binding("ctrl+q", "quit", "退出", show=True, priority=True),
    ]

    def __init__(self, config: dict):
        super().__init__()
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        self._tui_log_file = self._open_tui_log()

        self.agent = AgentCore(config)
        self.agent.mcp_manager.errlog = self._tui_log_file
        self.config = config
        self._sending = False
        self._cancel_requested = False
        self._last_ai_reply = ""
        self._show_thinking = True
        self._spinner_idx = 0
        self._marquee_pos = 0
        self._spinner_timer = None
        self._send_start_time: float = 0.0
        self._last_elapsed: float = 0.0

        self.agent.approval_callback = self._request_tool_approval

    @staticmethod
    def _open_tui_log():
        log_dir = Path.home() / ".nb_agent" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        return open(log_dir / "tui_stdout.log", "a", encoding="utf-8")

    def _redirect_all_handlers(self):
        """将所有指向终端的 logging handler 和 nb_log 缓存引用重定向到 TUI 日志文件。

        不动 sys.stdout（Textual 需要它来渲染界面），
        只在 handler 和 nb_log 内部引用层面拦截。
        """
        import logging
        log_file = self._tui_log_file
        log_write = log_file.write

        for logger_obj in [logging.getLogger()] + list(logging.Logger.manager.loggerDict.values()):
            if not isinstance(logger_obj, logging.Logger):
                continue
            for h in logger_obj.handlers:
                if hasattr(h, 'stream') and h.stream in (self._original_stdout, self._original_stderr):
                    h.stream = log_file

        try:
            import nb_log.monkey_sys_std as _std_mod
            _std_mod.stdout_raw = log_write
            _std_mod.stderr_raw = log_write
            import nb_log
            nb_log.stdout_raw = log_write
            nb_log.stderr_raw = log_write
        except (ImportError, AttributeError):
            pass

        try:
            import nb_log.monkey_print as _print_mod
            _print_mod.print_raw = lambda *a, **kw: print(*a, **kw, file=log_file)
        except (ImportError, AttributeError):
            pass

    def _restore_stdio(self):
        if self._tui_log_file and not self._tui_log_file.closed:
            self._tui_log_file.close()

    async def _request_tool_approval(self, tool_name: str, tool_args: dict) -> bool:
        future: asyncio.Future[bool] = asyncio.get_running_loop().create_future()

        def on_result(approved: Optional[bool]) -> None:
            if not future.done():
                future.set_result(bool(approved))

        self.push_screen(ToolApprovalScreen(tool_name, tool_args), on_result)
        return await future

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Horizontal(id="main-area"):
            yield RichLog(id="chat-panel", wrap=True, markup=True, highlight=True, auto_scroll=True)
            yield ToolPanel(self.agent, id="tool-panel")
        yield ChatInput(id="user-input")
        with Horizontal(id="ai-status-row"):
            yield Static("", id="ai-status-bar")
            yield Static("", id="ai-timer")
        yield Footer()

    async def on_mount(self):
        self._redirect_all_handlers()

        chat = self.query_one("#chat-panel", RichLog)
        model = self.agent.get_model_name()
        total = len(self.agent.available_models)
        chat.write(f"[bold #00d4aa]nb_agent[/bold #00d4aa] | 模型: [bold #4d96ff]{model}[/bold #4d96ff] | 共 [#ffd93d]{total}[/#ffd93d] 个可用模型")
        chat.write("[#6b7394]Enter=换行 | Ctrl+J/Ctrl+Enter=发送 | Tab=切换模型 | @=补全 | Ctrl+P=命令面板 | F1=帮助[/#6b7394]\n")
        self._update_subtitle()
        self.query_one("#user-input", ChatInput).focus()

        mcp_config = self.config.get("mcp", {})
        enabled_count = sum(1 for v in mcp_config.values() if v.get("enabled", True))
        if enabled_count > 0:
            chat.write(f"[#ff922b]⟳ {enabled_count} 个 MCP Server 后台连接中...[/#ff922b]")
            self.run_worker(self._connect_mcp_background(), exclusive=False)

    async def _connect_mcp_background(self):
        await self.agent.connect_mcp()
        chat = self.query_one("#chat-panel", RichLog)
        status = self.agent.get_mcp_status()
        ok = sum(1 for s in status if s["connected"])
        fail = len(status) - ok
        if ok > 0:
            chat.write(f"[#6bcb77]✓ {ok} 个 MCP Server 已连接[/#6bcb77]")
        if fail > 0:
            for s in status:
                if not s["connected"]:
                    chat.write(f"[#ff6b6b]✗ {s['name']}: {s['error']}[/#ff6b6b]")
        self.query_one("#tool-panel", ToolPanel).update_content()

    def _update_subtitle(self):
        agent_name = self.agent.current_agent_name or "默认助手"
        session_title = self.agent.session_store.get_session_title(self.agent.session_id)
        if session_title and session_title != "新会话":
            self.sub_title = f"Agent: {agent_name} | {session_title}"
            self._set_terminal_title(f"nb_agent - {agent_name} - {session_title}")
        else:
            self.sub_title = f"Agent: {agent_name}"
            self._set_terminal_title(f"nb_agent - {agent_name}")

    @staticmethod
    def _set_terminal_title(title: str):
        sys.stdout.write(f"\x1b]2;{title}\x07")
        sys.stdout.flush()

    # ─── 思考动画 ───────────────────────────────────────

    def _start_thinking_animation(self) -> None:
        self._spinner_idx = 0
        self._marquee_pos = 0
        if self._spinner_timer is not None:
            self._spinner_timer.stop()
        self._spinner_timer = self.set_interval(0.12, self._tick_spinner)

    def _stop_thinking_animation(self) -> None:
        if self._spinner_timer is not None:
            self._spinner_timer.stop()
            self._spinner_timer = None
        try:
            self.query_one("#ai-status-bar", Static).update("")
            self.query_one("#ai-timer", Static).update("")
        except Exception:
            pass

    def _tick_spinner(self) -> None:
        if not self._sending:
            self._stop_thinking_animation()
            return

        frame = _SPINNER_BIG[self._spinner_idx % len(_SPINNER_BIG)]
        base = f"  {frame}  AI is thinking...  Ctrl+K stop  *  "
        pos = self._marquee_pos % len(base)
        shifted = base[pos:] + base[:pos]
        full = (shifted * 6)[:120]

        marquee = Text()
        color_step = self._spinner_idx * 2
        for i, char in enumerate(full):
            color = _RAINBOW_COLORS[(i + color_step) % len(_RAINBOW_COLORS)]
            marquee.append(char, style=f"bold {color} on #0a0015")

        elapsed = time.monotonic() - self._send_start_time
        if elapsed < 60:
            time_val = f"{elapsed:.1f}s"
        elif elapsed < 3600:
            time_val = f"{int(elapsed // 60)}m{elapsed % 60:.0f}s"
        else:
            time_val = f"{int(elapsed // 3600)}h{int(elapsed % 3600 // 60)}m"

        spin_chars = _SPINNER_FRAMES
        spin = spin_chars[self._spinner_idx % len(spin_chars)]
        pulse = ["#ffd700", "#ff6b00", "#ff0080", "#a855f7", "#00d4ff", "#00ff88", "#ffd700"]
        tc = pulse[self._spinner_idx % len(pulse)]
        timer = Text()
        timer.append(f" {spin} ", style=f"bold {tc} on #0d0020")
        timer.append(f"{time_val} ", style=f"bold {tc} on #0d0020")

        self._spinner_idx += 1
        self._marquee_pos += 2
        try:
            self.query_one("#ai-status-bar", Static).update(marquee)
            self.query_one("#ai-timer", Static).update(timer)
        except Exception:
            pass

    # ─── 消息发送 ───────────────────────────────────────

    async def _do_send(self, user_text: str):
        chat = self.query_one("#chat-panel", RichLog)
        is_first_msg = len([m for m in self.agent.messages if m.get("role") == "user"]) == 0
        self._cancel_requested = False
        self._send_start_time = time.monotonic()
        self._start_thinking_animation()

        chat.write(Panel(
            Text(user_text, style="bold #f0f0f0 on #1a2744", overflow="fold"),
            border_style="bold #00d4ff",
            title="[bold #00d4ff]💎 user[/bold #00d4ff]",
            title_align="left",
            subtitle="[dim #00d4ff]━━━[/dim #00d4ff]",
            subtitle_align="right",
            padding=(0, 1),
        ))
        chat.write(f"[#7c3aed]({self.agent.get_model_name()}) 思考中...[/#7c3aed]")

        skill_context = self._extract_skill_mentions(user_text)
        if skill_context:
            self.agent.messages.append({"role": "system", "content": skill_context})

        try:
            use_stream = self.config.get("agent", {}).get("streaming", True)
            if use_stream:
                await self._handle_stream(user_text, chat)
            else:
                await self._handle_non_stream(user_text, chat)
        except Exception as e:
            chat.write(f"[#ff6b6b]发送失败: {type(e).__name__}: {e}[/#ff6b6b]")
        finally:
            self._stop_thinking_animation()
            self._sending = False
            try:
                self.query_one("#tool-panel", ToolPanel).update_content(last_elapsed=self._last_elapsed)
                self.query_one("#user-input", ChatInput).focus()
            except Exception:
                pass

        if is_first_msg:
            self._update_subtitle()
            self.run_worker(self._generate_title(), exclusive=False)

    async def _generate_title(self):
        try:
            await self.agent.generate_smart_title()
            self._update_subtitle()
        except Exception:
            pass

    def _is_at_bottom(self, chat: RichLog) -> bool:
        return chat.scroll_y >= chat.max_scroll_y - 2

    def _smart_scroll(self, chat: RichLog):
        if self._is_at_bottom(chat):
            chat.scroll_end(animate=False)

    async def _handle_stream(self, user_text: str, chat: RichLog):
        chat.auto_scroll = False
        model_label = self.agent.get_model_name()
        chat.write(f"[bold #4d96ff]🤖 {model_label}[/bold #4d96ff]")
        self._smart_scroll(chat)
        line_buffer = ""
        in_thinking = False
        full_reply_lines = []

        cancelled = False
        async for chunk in self.agent.chat_stream(user_text):
            if self._cancel_requested:
                cancelled = True
                break
            line_buffer += chunk
            await asyncio.sleep(0)

            if "<think>" in line_buffer and not in_thinking:
                in_thinking = True
                line_buffer = line_buffer.replace("<think>", "")
                if self._show_thinking:
                    chat.write("[italic #a78bfa]💭 思考过程:[/italic #a78bfa]")
                    self._smart_scroll(chat)

            if "</think>" in line_buffer and in_thinking:
                in_thinking = False
                before = line_buffer.split("</think>")[0]
                after = line_buffer.split("</think>", 1)[1]
                if self._show_thinking:
                    for line in before.split("\n"):
                        if line.strip():
                            chat.write(Text(line, style="#a78bfa"))
                    chat.write("[italic #7c3aed]── 思考结束 ──[/italic #7c3aed]")
                    self._smart_scroll(chat)
                line_buffer = after.lstrip("\n")
                continue

            while "\n" in line_buffer:
                line, line_buffer = line_buffer.split("\n", 1)
                if in_thinking and not self._show_thinking:
                    continue
                if not line.strip() and in_thinking:
                    continue
                if in_thinking:
                    chat.write(Text(line, style="#a78bfa"))
                elif line.strip():
                    chat.write(Text(line))
                    full_reply_lines.append(line)
                self._smart_scroll(chat)

        if cancelled:
            chat.write("[#ff6b6b]⏹ 已终止回答[/#ff6b6b]")
            self._cancel_requested = False
        else:
            if line_buffer:
                if in_thinking and self._show_thinking:
                    chat.write(Text(line_buffer, style="#a78bfa"))
                elif not in_thinking:
                    chat.write(Text(line_buffer))
                    full_reply_lines.append(line_buffer)

        self._last_ai_reply = "\n".join(full_reply_lines)

        if not cancelled:
            self._redraw_chat()
            chat = self.query_one("#chat-panel", RichLog)

        elapsed = time.monotonic() - self._send_start_time
        self._last_elapsed = elapsed
        t = self.agent.get_token_usage()
        rounds_str = f" | 交互{t['last_rounds']}轮" if t['last_rounds'] > 1 else ""
        tc_str = f" | 工具{t['last_tool_calls']}次" if t['last_tool_calls'] > 0 else ""
        chat.write(f"[#6b7394](本次 入{_fmt_tokens(t['last_prompt'])}+出{_fmt_tokens(t['last_completion'])}={_fmt_tokens(t['last_total'])} | 耗时{elapsed:.1f}s{rounds_str}{tc_str} | 累计 {_fmt_tokens(t['total'])})[/#6b7394]")
        chat.auto_scroll = True
        chat.scroll_end(animate=False)

    async def _handle_non_stream(self, user_text: str, chat: RichLog):
        response = await self.agent.chat(user_text)

        for tc in response.tool_calls:
            chat.write(Panel(
                Text(tc.args, style="#fbbf24", overflow="fold"),
                border_style="#d97706",
                title=f"[bold #fbbf24]🔧 {tc.name}[/bold #fbbf24]",
                title_align="left",
                padding=(0, 1),
            ))
            result = tc.result[:5000] if len(tc.result) > 5000 else tc.result
            chat.write(Panel(
                Text(result, style="#86efac", overflow="fold"),
                border_style="#22c55e",
                title="[bold #86efac]📋 返回结果[/bold #86efac]",
                title_align="left",
                padding=(0, 1),
            ))

        if response.reasoning and self._show_thinking:
            chat.write(Panel(
                Text(response.reasoning, style="italic #a78bfa", overflow="fold"),
                border_style="#7c3aed",
                title="[bold #a78bfa]💭 思考过程[/bold #a78bfa]",
                title_align="left",
                padding=(0, 1),
            ))

        model_label = self.agent.get_model_name()
        chat.write(f"[bold #4d96ff]🤖 {model_label}[/bold #4d96ff]")
        chat.write(RichMarkdown(response.text))
        self._last_ai_reply = response.text
        elapsed = time.monotonic() - self._send_start_time
        self._last_elapsed = elapsed
        t = self.agent.get_token_usage()
        rounds_str = f" | 交互{t['last_rounds']}轮" if t['last_rounds'] > 1 else ""
        tc_str = f" | 工具{t['last_tool_calls']}次" if t['last_tool_calls'] > 0 else ""
        chat.write(f"[#6b7394](本次 入{_fmt_tokens(t['last_prompt'])}+出{_fmt_tokens(t['last_completion'])}={_fmt_tokens(t['last_total'])} | 耗时{elapsed:.1f}s{rounds_str}{tc_str} | 累计 {_fmt_tokens(t['total'])})[/#6b7394]")

    # ─── 快捷键 Actions ────────────────────────────────

    def action_stop_ai(self):
        if isinstance(self.screen, ModalScreen):
            self.screen.dismiss()
            return
        if self._sending:
            self._cancel_requested = True
            self.notify("正在终止 AI 回答...", timeout=2)

    def action_edit_last(self):
        if self._sending:
            self.notify("请等待 AI 回答完成", severity="warning", timeout=2)
            return
        self._edit_last_message()

    async def action_send_msg(self):
        if self._sending:
            return
        input_widget = self.query_one("#user-input", ChatInput)
        user_text = input_widget.text.strip()
        if not user_text:
            return
        input_widget.clear()
        self._sending = True
        self.run_worker(self._do_send(user_text), exclusive=False)

    def action_new_session(self):
        if self._sending:
            self.notify("请等待 AI 回答完成", severity="warning", timeout=2)
            return
        self._cmd_new_session()

    def action_resume_session(self):
        self.push_screen(SessionSelectScreen(self.agent), self._on_session_selected)

    def action_show_help(self):
        self.push_screen(HelpScreen())

    def action_toggle_input(self):
        input_widget = self.query_one("#user-input", ChatInput)
        input_widget.toggle_class("expanded")
        input_widget.focus()

    def action_show_skills(self):
        self.push_screen(SkillListScreen(self.agent), self._on_skill_selected)

    def action_show_agents(self):
        self.push_screen(AgentSelectScreen(self.agent), self._on_agent_selected)

    def _on_agent_selected(self, result: str):
        if not result:
            self.query_one("#user-input", ChatInput).focus()
            return
        if result == "__new__":
            self._cmd_new_agent()
            return
        if result.startswith("__edit__:"):
            self._cmd_edit_agent(result[9:])
            return
        if result.startswith("__copy__:"):
            self._cmd_copy_agent(result[9:])
            return
        if result == self.agent.current_agent_id:
            self.notify("已是当前 Agent", timeout=2)
            self.query_one("#user-input", ChatInput).focus()
            return
        self.agent.apply_agent(result)
        chat = self.query_one("#chat-panel", RichLog)
        chat.clear()
        chat.write(f"[bold #a78bfa]✦ 已应用 Agent: {self.agent.current_agent_name}[/bold #a78bfa]")
        chat.write(f"[#6b7394]System prompt + 工具配置已更新，新会话已创建[/#6b7394]\n")
        self.query_one("#tool-panel", ToolPanel).update_content()
        self._update_subtitle()
        self.query_one("#user-input", ChatInput).focus()

    def _cmd_new_agent(self):
        self.push_screen(
            AgentEditScreen(self.agent),
            self._on_agent_saved,
        )

    def _cmd_edit_agent(self, agent_id: str):
        agents = self.agent.get_agents()
        for a in agents:
            if a["id"] == agent_id:
                self.push_screen(
                    AgentEditScreen(self.agent, edit_agent=a),
                    self._on_agent_saved,
                )
                return

    def _cmd_copy_agent(self, agent_id: str):
        agents = self.agent.get_agents()
        for a in agents:
            if a["id"] == agent_id:
                copy_data = dict(a)
                copy_data["id"] = ""
                copy_data["name"] = f"{a['name']} (副本)"
                copy_data["is_builtin"] = False
                self.push_screen(
                    AgentEditScreen(self.agent, edit_agent=copy_data),
                    self._on_agent_saved,
                )
                return

    def _on_agent_saved(self, result: str):
        if not result:
            self.query_one("#user-input", ChatInput).focus()
            return
        import json as _json
        try:
            data = _json.loads(result)
        except Exception:
            return
        edit_id = data.get("edit_id", "")
        name = data["name"]
        prompt = data["system_prompt"]
        atg = data.get("allowed_tool_groups")
        ams = data.get("allowed_mcp_servers")
        ask = data.get("allowed_skills")
        if edit_id:
            self.agent.update_agent(edit_id, name, prompt, atg, ams, ask)
            self.notify(f"已更新 Agent: {name}", timeout=3)
        else:
            self.agent.save_agent(name, prompt, atg, ams, ask)
            self.notify(f"已创建 Agent: {name}", timeout=3)
        self.query_one("#user-input", ChatInput).focus()

    def on_chat_input_mention_triggered(self, event: ChatInput.MentionTriggered) -> None:
        candidates = self._build_mention_candidates()
        if candidates:
            self.push_screen(MentionSelectScreen(candidates), self._on_mention_selected)

    def _build_mention_candidates(self) -> list:
        candidates = []
        for t in self.agent.get_tools():
            if t["name"] == "view_skill" or t.get("disabled"):
                continue
            candidates.append({
                "name": t["name"],
                "func_name": t.get("func_name", t["name"]),
                "group": t.get("group", ""),
                "description": t["description"],
                "type": "tool",
                "source": t["source"],
            })
        for s in self.agent.skill_manager.get_all_skills():
            candidates.append({
                "name": s["name"],
                "description": s["description"],
                "type": "skill",
                "source": "Skill",
                "manual_only": s.get("manual_only", False),
            })
        return candidates

    def _on_mention_selected(self, prefixed_name: str) -> None:
        input_widget = self.query_one("#user-input", ChatInput)
        if prefixed_name:
            input_widget.insert(prefixed_name + " ")
        input_widget.focus()

    def action_clear_chat(self):
        if self._sending:
            self.notify("请等待 AI 回答完成", severity="warning", timeout=2)
            return
        chat = self.query_one("#chat-panel", RichLog)
        chat.clear()
        self.agent.clear_history()
        chat.write("[#6b7394]对话已清空，上下文已重置[/#6b7394]\n")

    def action_select_model(self):
        self.push_screen(ModelSelectScreen(self.agent), self._on_model_selected)

    async def on_unmount(self):
        await self.agent.disconnect_mcp()
        self._restore_stdio()

    # ─── 命令面板回调 ──────────────────────────────────

    def _cmd_new_session(self):
        chat = self.query_one("#chat-panel", RichLog)
        self.agent.clear_history()
        chat.clear()
        chat.write("[#6b7394]✦ 新会话已创建，上下文已重置[/#6b7394]\n")
        self.query_one("#tool-panel", ToolPanel).update_content()
        self._update_subtitle()

    def _cmd_toggle_thinking(self):
        self._show_thinking = not self._show_thinking
        state = "显示" if self._show_thinking else "隐藏"
        self._redraw_chat()
        self.notify(f"思考过程已{state}", timeout=2)

    def _cmd_export_markdown(self):
        self.push_screen(RoundsInputScreen("导出 Markdown 文件"), self._on_export_rounds)

    def _cmd_copy_markdown(self):
        self.push_screen(RoundsInputScreen("复制为 Markdown"), self._on_copy_rounds)

    # ─── 弹窗回调 ──────────────────────────────────────

    def _on_model_selected(self, model_name):
        if not model_name:
            self.query_one("#user-input", ChatInput).focus()
            return
        old = self.agent.get_model_name()
        if self.agent.switch_model(model_name):
            new = self.agent.get_model_name()
            chat = self.query_one("#chat-panel", RichLog)
            chat.write(f"\n[bold #ffd93d]✦ 模型已切换:[/bold #ffd93d] [#6b7394]{old}[/#6b7394] → [bold #00d4aa]{new}[/bold #00d4aa]")
            self._update_subtitle()
            self.query_one("#tool-panel", ToolPanel).update_content()
        self.query_one("#user-input", ChatInput).focus()

    def _on_skill_selected(self, skill_name):
        if not skill_name:
            self.query_one("#user-input", ChatInput).focus()
            return
        if skill_name.startswith("__apply__:"):
            real_name = skill_name[10:]
            input_widget = self.query_one("#user-input", ChatInput)
            input_widget.insert(f"@skill:{real_name} ")
            input_widget.focus()
            self.notify(f"已插入 @skill:{real_name}，输入消息后发送即可", timeout=3)
            return
        skill_data = self.agent.skill_manager.view_skill(skill_name)
        if skill_data.get("success"):
            self.push_screen(SkillContentScreen(skill_data))
        else:
            self.notify(skill_data.get("error", "加载失败"), severity="warning", timeout=3)
        self.query_one("#user-input", ChatInput).focus()

    def _on_session_selected(self, session_id):
        if not session_id:
            self.query_one("#user-input", ChatInput).focus()
            return
        if session_id == self.agent.session_id:
            self.notify("已是当前会话", timeout=2)
            self.query_one("#user-input", ChatInput).focus()
            return
        sessions = self.agent.get_session_list(20)
        title = ""
        for s in sessions:
            if s["id"] == session_id:
                title = s["title"]
                break
        self.run_worker(self._cmd_resume_session(session_id, title), exclusive=False)
        self.query_one("#user-input", ChatInput).focus()

    async def _cmd_resume_session(self, session_id: str, title: str):
        chat = self.query_one("#chat-panel", RichLog)
        msgs = self.agent.session_store.get_messages(session_id)
        self.agent.session_id = session_id
        self.agent.messages = [{"role": "system", "content": self.agent.system_prompt}]
        for m in msgs:
            self.agent.messages.append({"role": m["role"], "content": m["content"]})
        chat.clear()
        chat.write(f"[#6bcb77]✦ 已恢复会话: {title}[/#6bcb77]")
        for m in msgs:
            if m["role"] == "user":
                chat.write(Panel(
                    Text(m["content"], style="bold #f0f0f0 on #1a2744", overflow="fold"),
                    border_style="bold #00d4ff",
                    title="[bold #00d4ff]💎 user[/bold #00d4ff]",
                    title_align="left",
                    subtitle="[dim #00d4ff]━━━[/dim #00d4ff]",
                    subtitle_align="right",
                    padding=(0, 1),
                ))
            elif m["role"] == "assistant" and m["content"]:
                chat.write("[bold #4d96ff]🤖 AI[/bold #4d96ff]")
                chat.write(RichMarkdown(m["content"]))
        self._update_subtitle()

    def _on_export_rounds(self, rounds):
        if rounds is None or rounds < 0:
            return
        self._export_markdown(rounds)

    def _on_copy_rounds(self, rounds):
        if rounds is None or rounds < 0:
            return
        self._copy_markdown(rounds)

    # ─── 编辑 / 导出 / 复制 ────────────────────────────

    def _edit_last_message(self):
        msgs = self.agent.messages
        last_user_idx = -1
        for i in range(len(msgs) - 1, -1, -1):
            if msgs[i].get("role") == "user":
                last_user_idx = i
                break
        if last_user_idx < 0:
            self.notify("没有可编辑的消息", severity="warning", timeout=2)
            return
        last_user_text = msgs[last_user_idx].get("content", "")
        self.agent.messages = msgs[:last_user_idx]
        input_widget = self.query_one("#user-input", ChatInput)
        input_widget.clear()
        input_widget.insert(last_user_text)
        input_widget.focus()
        self._redraw_chat()
        self.notify("已撤回上轮对话，可编辑后重新发送", timeout=3)

    def _show_tool_details(self):
        self.push_screen(ToolDetailScreen(self.agent))

    def _get_round_messages(self, rounds: int = 0) -> list:
        """获取最近 N 轮对话的消息列表，rounds=0 返回全部"""
        messages = self.agent.messages
        if rounds <= 0:
            return messages
        user_count = 0
        start_idx = 0
        for i in range(len(messages) - 1, -1, -1):
            if messages[i].get("role") == "user":
                user_count += 1
                if user_count == rounds:
                    start_idx = i
                    break
        if user_count < rounds:
            start_idx = 0
        result = [m for m in messages if m.get("role") == "system"]
        result.extend(m for i, m in enumerate(messages) if m.get("role") != "system" and i >= start_idx)
        return result

    def _export_markdown(self, rounds: int = 0):
        messages = self._get_round_messages(rounds)
        session_title = self.agent.session_store.get_session_title(self.agent.session_id) or ""
        display_title = session_title if session_title and session_title != "新会话" else f"会话 {self.agent.session_id[:8]}"
        lines = [f"# {display_title}\n"]
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "") or ""
            if role == "system":
                continue
            elif role == "user":
                lines.append(f"## 用户\n\n{content}\n")
            elif role == "assistant":
                reasoning = msg.get("reasoning_content", "")
                if reasoning:
                    lines.append(f"<details><summary>💭 思考过程</summary>\n\n{reasoning}\n\n</details>\n")
                tool_calls = msg.get("tool_calls", [])
                for tc in tool_calls:
                    func = tc.get("function", {})
                    name = func.get("name", "?")
                    args = func.get("arguments", "{}")
                    lines.append(f"### 🔧 调用工具: {name}\n\n```json\n{args}\n```\n")
                if content:
                    lines.append(f"## AI\n\n{content}\n")
            elif role == "tool":
                tool_name = msg.get("name", "tool")
                lines.append(f"> 📋 **{tool_name} 返回**: {content}\n")

        if len(lines) <= 1:
            self.notify("没有对话内容", severity="warning", timeout=2)
            return

        save_dir = os.path.join(Path.home(), ".nb_agent", "exports")
        os.makedirs(save_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if session_title and session_title != "新会话":
            safe_title = re.sub(r'[\\/:*?"<>|\s]+', '_', session_title)[:50].strip('_')
            filename = f"chat_{timestamp}_{safe_title}.md"
        else:
            filename = f"chat_{timestamp}_{self.agent.session_id[:8]}.md"
        filepath = os.path.join(save_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        self.notify(f"已导出: {filepath}", timeout=4)

    def _copy_markdown(self, rounds: int = 0):
        messages = self._get_round_messages(rounds)
        lines = []
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "") or ""
            if role == "system":
                continue
            elif role == "user":
                lines.append(f"## 用户\n\n{content}\n")
            elif role == "assistant":
                reasoning = msg.get("reasoning_content", "")
                if reasoning:
                    lines.append(f"<details><summary>💭 思考过程</summary>\n\n{reasoning}\n\n</details>\n")
                tool_calls = msg.get("tool_calls", [])
                for tc in tool_calls:
                    func = tc.get("function", {})
                    name = func.get("name", "?")
                    args = func.get("arguments", "{}")
                    lines.append(f"### 🔧 调用工具: {name}\n\n```json\n{args}\n```\n")
                if content:
                    lines.append(f"## AI\n\n{content}\n")
            elif role == "tool":
                tool_name = msg.get("name", "tool")
                lines.append(f"> 📋 **{tool_name} 返回**: {content}\n")

        if not lines:
            self.notify("没有对话内容", severity="warning", timeout=2)
            return
        self.copy_to_clipboard("\n".join(lines))
        rounds_hint = f"最近 {rounds} 轮" if rounds > 0 else "全部"
        self.notify(f"{rounds_hint}对话 Markdown 已复制到剪贴板", timeout=3)

    # ─── @ mention 预处理 ──────────────────────────────

    def _extract_skill_mentions(self, text: str) -> str:
        """从消息中提取 @skill:name 引用，加载 SKILL.md 内容作为临时系统指令。"""
        skill_mentions = re.findall(r'@skill:([\w-]+)', text)
        if not skill_mentions:
            return ""

        injected = []
        for name in skill_mentions:
            skill_data = self.agent.skill_manager.view_skill(name)
            if skill_data.get("success"):
                injected.append(
                    f"[Skill: {name}]\n"
                    f"以下是 Skill '{name}' 的指导文档，请据此完成任务：\n\n"
                    f"{skill_data['content']}"
                )
        return "\n\n---\n".join(injected) if injected else ""

    # ─── 聊天重绘 ──────────────────────────────────────

    def _redraw_chat(self):
        chat = self.query_one("#chat-panel", RichLog)
        chat.clear()
        total = len(self.agent.available_models)
        chat.write(f"[bold #00d4aa]nb_agent[/bold #00d4aa] | 共 [#ffd93d]{total}[/#ffd93d] 个可用模型")
        chat.write("[#6b7394]Enter=换行 | Ctrl+J/Ctrl+Enter=发送 | Ctrl+↑=编辑上条 | F1=帮助[/#6b7394]\n")

        last_assistant_idx = -1
        for i in range(len(self.agent.messages) - 1, -1, -1):
            if self.agent.messages[i].get("role") == "assistant" and self.agent.messages[i].get("reasoning_content"):
                last_assistant_idx = i
                break

        for idx, msg in enumerate(self.agent.messages):
            role = msg.get("role", "")
            content = msg.get("content", "") or ""
            if role == "system":
                continue
            elif role == "user":
                chat.write(Panel(
                    Text(content, style="bold #f0f0f0 on #1a2744", overflow="fold"),
                    border_style="bold #00d4ff",
                    title="[bold #00d4ff]💎 user[/bold #00d4ff]",
                    title_align="left",
                    subtitle="[dim #00d4ff]━━━[/dim #00d4ff]",
                    subtitle_align="right",
                    padding=(0, 1),
                ))
            elif role == "assistant":
                tool_calls = msg.get("tool_calls", [])
                reasoning = msg.get("reasoning_content", "")
                if tool_calls or content or reasoning:
                    model_label = msg.get("_model") or "AI"
                    chat.write(f"[bold #4d96ff]🤖 {model_label}[/bold #4d96ff]")
                if reasoning and self._show_thinking:
                    is_last = (idx == last_assistant_idx)
                    if is_last:
                        chat.write(Panel(
                            Text(reasoning, style="italic #a78bfa", overflow="fold"),
                            border_style="#7c3aed",
                            title="[bold #a78bfa]💭 思考过程[/bold #a78bfa]",
                            title_align="left",
                            padding=(0, 1),
                        ))
                    else:
                        char_count = len(reasoning)
                        chat.write(f"  [italic #7c3aed]💭 思考了 {char_count} 字 (Ctrl+P→切换思考显示 可查看全部)[/italic #7c3aed]")
                if tool_calls:
                    for tc in tool_calls:
                        func = tc.get("function", {})
                        name = func.get("name", "?")
                        args = func.get("arguments", "{}")
                        chat.write(Panel(
                            Text(args, style="#fbbf24", overflow="fold"),
                            border_style="#d97706",
                            title=f"[bold #fbbf24]🔧 {name}[/bold #fbbf24]",
                            title_align="left",
                            padding=(0, 1),
                        ))
                if content:
                    chat.write(RichMarkdown(content))
            elif role == "tool":
                result = content[:5000] if len(content) > 5000 else content
                tool_name = msg.get("name", "tool")
                chat.write(Panel(
                    Text(result, style="#86efac", overflow="fold"),
                    border_style="#22c55e",
                    title=f"[bold #86efac]📋 {tool_name} 返回[/bold #86efac]",
                    title_align="left",
                    padding=(0, 1),
                ))
