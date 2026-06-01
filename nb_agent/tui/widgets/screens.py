"""TUI 弹窗：模型选择、帮助、会话恢复、工具详情、轮次输入、工具审批"""

import json
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Input, OptionList, Static
from textual.widgets.option_list import Option
from textual.binding import Binding
from textual.screen import ModalScreen
from rich.text import Text

from nb_agent.core import AgentCore


class ModelSelectScreen(ModalScreen[str]):
    """模型选择弹窗"""

    BINDINGS = [
        Binding("escape", "dismiss_modal", "返回"),
    ]

    def __init__(self, agent: AgentCore, **kwargs):
        super().__init__(**kwargs)
        self.agent = agent

    def compose(self) -> ComposeResult:
        with Vertical(id="model-dialog"):
            yield Static("[bold]选择模型[/bold]  (↑↓选择, Enter确认, Esc返回)\n", id="model-title")
            yield OptionList(id="model-list")

    def on_mount(self):
        option_list = self.query_one("#model-list", OptionList)
        grouped = self.agent.get_models_grouped()
        current = self.agent.get_model_name()

        for provider_name, models in grouped.items():
            option_list.add_option(Option(
                Text(f"── {provider_name} ──", style="dim #6b7394"), disabled=True
            ))
            for m in models:
                if m.id == current:
                    label = Text(f"  ▶ {m.id} ({m.name})", style="bold #00d4aa")
                else:
                    label = Text(f"    {m.id} ({m.name})", style="#c0c0c0")
                option_list.add_option(Option(label, id=m.id))

        option_list.focus()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected):
        if event.option.id:
            self.dismiss(event.option.id)

    def action_dismiss_modal(self):
        self.dismiss("")


class HelpScreen(ModalScreen):
    """帮助弹窗"""

    BINDINGS = [
        Binding("escape", "dismiss_modal", "返回"),
        Binding("f1", "dismiss_modal", "返回"),
        Binding("enter", "dismiss_modal", "返回"),
    ]

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="help-dialog"):
            yield Static(self._build_help(), id="help-content")

    def _build_help(self) -> str:
        lines = []
        lines.append("[bold #00d4aa]═══ nb_agent 帮助 ═══[/bold #00d4aa]\n")

        lines.append("[bold #ffd93d]⌨ 快捷键[/bold #ffd93d]")
        keys = [
            ("Ctrl+J / Ctrl+Enter", "发送消息"),
            ("Enter", "输入框内换行"),
            ("Tab", "打开模型选择弹窗"),
            ("Ctrl+N", "新建会话"),
            ("Ctrl+K", "终止当前 AI 回答"),
            ("Ctrl+↑", "编辑上一轮提问"),
            ("Ctrl+R", "恢复历史会话"),
            ("Ctrl+E", "展开/收起输入框"),
            ("Ctrl+L", "清空屏幕"),
            ("Ctrl+P", "打开命令面板"),
            ("F1", "显示此帮助"),
            ("F2", "查看 Skills 列表"),
            ("F4", "Agent 管理（提示词+工具配置）"),
            ("Ctrl+Q", "退出程序"),
        ]
        for key, desc in keys:
            lines.append(f"  [#ffd93d]{key:<20}[/#ffd93d] [#c0c0c0]{desc}[/#c0c0c0]")

        lines.append("")
        lines.append("[bold #4d96ff]📋 命令面板 (Ctrl+P)[/bold #4d96ff]")
        cmds = [
            ("编辑上轮提问", "撤回最后一轮，重新编辑"),
            ("切换思考显示", "显示或隐藏 AI 思考过程"),
            ("查看工具详情", "查看所有工具完整描述"),
            ("复制完整对话", "复制 Markdown 到剪贴板"),
            ("复制最后回复", "复制到剪贴板"),
            ("导出/保存", "导出 .md 或保存 .txt"),
        ]
        for name, desc in cmds:
            lines.append(f"  [#4d96ff]{name:<18}[/#4d96ff] [#c0c0c0]{desc}[/#c0c0c0]")

        lines.append("")
        lines.append("[bold #ff922b]📋 复制文本[/bold #ff922b]")
        lines.append("  [#c0c0c0]• Shift+鼠标左键拖选 → 选中文本，然后 Ctrl+C 复制[/#c0c0c0]")
        lines.append("  [#c0c0c0]• Alt+Shift+鼠标拖选  → 矩形区域选择[/#c0c0c0]")
        lines.append("  [#c0c0c0]• Ctrl+P → 复制完整对话 / 复制最后回复 (Markdown 格式)[/#c0c0c0]")

        lines.append("")
        lines.append("[bold #6bcb77]💡 提示[/bold #6bcb77]")
        lines.append("  [#c0c0c0]• 输入 @ 自动弹出工具/Skill 补全[/#c0c0c0]")
        lines.append("  [#c0c0c0]• @skill:name 注入 Skill 指南，@tool:name 提示 AI 用该工具[/#c0c0c0]")
        lines.append("  [#c0c0c0]• 右侧面板可点击切换：模型 / MCP Server / 工具分组[/#c0c0c0]")
        lines.append("  [#c0c0c0]• MCP 工具在后台自动连接[/#c0c0c0]")
        lines.append("  [#c0c0c0]• 对话超长时自动截断早期消息[/#c0c0c0]")

        lines.append("\n[dim #6b7394]按 Esc / Enter / F1 关闭[/dim #6b7394]")
        return "\n".join(lines)

    def action_dismiss_modal(self):
        self.dismiss()


class SessionSelectScreen(ModalScreen[str]):
    """会话选择弹窗"""

    BINDINGS = [
        Binding("escape", "dismiss_modal", "返回"),
    ]

    def __init__(self, agent: AgentCore, **kwargs):
        super().__init__(**kwargs)
        self.agent = agent
        self._session_ids = []

    def compose(self) -> ComposeResult:
        with Vertical(id="session-dialog"):
            yield Static("[bold]恢复会话[/bold]  (↑↓选择, Enter确认, Esc返回)\n", id="session-title")
            yield OptionList(id="session-list")

    def on_mount(self):
        option_list = self.query_one("#session-list", OptionList)
        sessions = self.agent.get_session_list(20)
        current_id = self.agent.session_id

        if not sessions:
            option_list.add_option(Option(
                Text("没有历史会话", style="dim #6b7394"), disabled=True
            ))
            return

        for s in sessions:
            title = s["title"]
            date = s["updated_at"][:16]
            sid = s["id"]
            self._session_ids.append(sid)

            if sid == current_id:
                label = Text(f"  ▶ {title}  ({date})", style="bold #00d4aa")
            else:
                label = Text(f"    {title}  ({date})", style="#c0c0c0")
            option_list.add_option(Option(label, id=sid))

        option_list.focus()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected):
        if event.option.id:
            self.dismiss(event.option.id)

    def action_dismiss_modal(self):
        self.dismiss("")


class ToolDetailScreen(ModalScreen):
    """工具详情弹窗"""

    BINDINGS = [
        Binding("escape", "dismiss_modal", "返回"),
        Binding("enter", "dismiss_modal", "返回"),
    ]

    def __init__(self, agent: AgentCore, **kwargs):
        super().__init__(**kwargs)
        self.agent = agent

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="tool-detail-dialog"):
            yield Static(self._build_content(), id="tool-detail-content")

    def _build_content(self) -> str:
        tools = self.agent.get_tools()
        enabled_count = sum(1 for t in tools if not t.get("disabled"))
        lines = [f"[bold #6bcb77]函数详情 ({enabled_count}/{len(tools)})[/bold #6bcb77]\n"]
        for t in tools:
            source = t.get("source", "")
            disabled = t.get("disabled", False)
            if disabled:
                icon = "[#ffd93d]○[/#ffd93d]"
                src_label = f"[#ffd93d]{source} [已禁用][/#ffd93d]"
                name_style = "#8890a8"
            elif source.startswith("MCP:"):
                icon = "[#b39ddb]◆[/#b39ddb]"
                src_label = f"[#b39ddb]{source}[/#b39ddb]"
                name_style = "#c0c0c0"
            elif source == "第三方":
                icon = "[#4d96ff]●[/#4d96ff]"
                src_label = f"[#4d96ff]{source}[/#4d96ff]"
                name_style = "#c0c0c0"
            else:
                icon = "[#6bcb77]●[/#6bcb77]"
                src_label = f"[#6bcb77]{source}[/#6bcb77]"
                name_style = "#c0c0c0"
            lines.append(f"{icon} [bold {name_style}]{t['name']}[/bold {name_style}]  {src_label}")
            lines.append(f"  [#8890a8]{t['description']}[/#8890a8]")
            lines.append("")
        lines.append("[dim #6b7394]按 Esc / Enter 关闭[/dim #6b7394]")
        return "\n".join(lines)

    def action_dismiss_modal(self):
        self.dismiss()


class RoundsInputScreen(ModalScreen[int]):
    """轮次输入弹窗：用户输入要导出/复制的对话轮次，0=全部"""

    BINDINGS = [
        Binding("escape", "cancel", "取消"),
    ]

    def __init__(self, action_name: str, **kwargs):
        super().__init__(**kwargs)
        self.action_name = action_name

    def compose(self) -> ComposeResult:
        with Vertical(id="rounds-dialog"):
            yield Static(f"[bold #ffd93d]{self.action_name}[/bold #ffd93d]", id="rounds-title")
            yield Static("[#c0c0c0]导出/复制最近 N 轮对话 (0 = 全部)[/#c0c0c0]", id="rounds-hint")
            yield Input(value="0", id="rounds-input")
            yield Static("[dim #6b7394]Enter 确认 | Esc 取消[/dim #6b7394]", id="rounds-footer")

    def on_mount(self):
        self.query_one("#rounds-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted):
        self._do_confirm(event.value)

    def action_confirm(self):
        text = self.query_one("#rounds-input", Input).value.strip()
        self._do_confirm(text)

    def _do_confirm(self, text: str):
        try:
            n = int(text.strip())
            if n < 0:
                n = 0
        except ValueError:
            n = 0
        self.dismiss(n)

    def action_cancel(self):
        self.dismiss(-1)


class SkillListScreen(ModalScreen[str]):
    """Skills 列表弹窗"""

    BINDINGS = [
        Binding("escape", "dismiss_modal", "返回"),
    ]

    def __init__(self, agent: AgentCore, **kwargs):
        super().__init__(**kwargs)
        self.agent = agent

    def compose(self) -> ComposeResult:
        with Vertical(id="skill-dialog"):
            yield Static(
                "[bold #ffa726]✦ Skills 列表[/bold #ffa726]  [dim #6b7394]↑↓ 选择 · 按钮操作 · Esc 返回[/dim #6b7394]",
                id="skill-title",
            )
            yield OptionList(id="skill-list")
            with Horizontal(id="skill-buttons"):
                yield Button("应用", id="btn-skill-apply", variant="success")
                yield Button("查看详情", id="btn-skill-view", variant="default")
                yield Button("使用说明", id="btn-skill-help", variant="default")
                yield Button("返回", id="btn-skill-back", variant="default")

    def on_mount(self):
        option_list = self.query_one("#skill-list", OptionList)
        all_skills = self.agent.skill_manager.get_all_skills()

        if not all_skills:
            option_list.add_option(Option(
                Text("没有发现 Skills", style="dim #6b7394"), disabled=True
            ))
            return

        for s in all_skills:
            name = s["name"]
            desc = s["description"]
            if len(desc) > 60:
                desc = desc[:60] + "..."
            manual = "  [仅手动]" if s.get("manual_only") else ""
            icon = "○" if s.get("manual_only") else "●"
            label = Text(f"  {icon} {name}{manual}  — {desc}", style="#c0c0c0")
            option_list.add_option(Option(label, id=name))

        option_list.focus()

    def _get_selected_skill_id(self) -> str:
        option_list = self.query_one("#skill-list", OptionList)
        idx = option_list.highlighted
        if idx is not None:
            opt = option_list.get_option_at_index(idx)
            if opt.id:
                return opt.id
        return ""

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn-skill-apply":
            skill_id = self._get_selected_skill_id()
            if skill_id:
                self.dismiss(f"__apply__:{skill_id}")
                return
            self.app.notify("请先选中一个 Skill", severity="warning", timeout=2)
        elif event.button.id == "btn-skill-view":
            skill_id = self._get_selected_skill_id()
            if skill_id:
                self.dismiss(skill_id)
                return
            self.app.notify("请先选中一个 Skill", severity="warning", timeout=2)
        elif event.button.id == "btn-skill-help":
            self.app.push_screen(_SkillHelpScreen())
        elif event.button.id == "btn-skill-back":
            self.dismiss("")
        self.query_one("#skill-list", OptionList).focus()

    def action_dismiss_modal(self):
        self.dismiss("")


class _SkillHelpScreen(ModalScreen):
    """Skills 使用说明弹窗"""

    BINDINGS = [
        Binding("escape", "dismiss_modal", "返回"),
        Binding("enter", "dismiss_modal", "返回"),
    ]

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="skill-content-dialog"):
            yield Static(self._build(), id="skill-help-text")

    def _build(self) -> str:
        lines = [
            "[bold #ffa726]═══ Skills 使用说明 ═══[/bold #ffa726]\n",
            "[bold #4d96ff]什么是 Skill？[/bold #4d96ff]",
            "  Skill 是一份 SKILL.md 格式的操作指南，告诉 AI 在特定",
            "  任务中如何一步步执行。AI 在需要时通过 view_skill 工具",
            "  主动查阅，实现渐进式披露（Progressive Disclosure）。\n",
            "[bold #4d96ff]开放标准[/bold #4d96ff]",
            "  遵循 Agent Skills 开放规范（agentskills.io）",
            "  由 Anthropic 创建，已被 26+ 平台采用：",
            "  Claude / OpenAI Codex / Gemini CLI / GitHub Copilot /",
            "  Cursor / VS Code / Microsoft Agent Framework 等\n",
            "[bold #4d96ff]渐进式披露（Progressive Disclosure）[/bold #4d96ff]",
            "  1. [#ffa726]Discovery[/#ffa726]：启动时仅加载 name + description",
            "  2. [#ffa726]Activation[/#ffa726]：任务匹配时加载完整 SKILL.md",
            "  3. [#ffa726]Execution[/#ffa726]：按需加载 scripts / references\n",
            "[bold #4d96ff]如何创建 Skill？[/bold #4d96ff]",
            "  1. 在 .nb_agent/skills/ 下新建文件夹",
            "  2. 在文件夹中创建 SKILL.md，格式如下：",
            "  [bold #ff5252]⚠ 文件夹名必须和 name 字段相同[/bold #ff5252]\n",
            "  [#c0c0c0]my-skill/[/#c0c0c0]",
            "  [#c0c0c0]└── SKILL.md[/#c0c0c0]\n",
            "  [#c0c0c0]---[/#c0c0c0]",
            "  [#c0c0c0]name: my-skill    ← 必须与文件夹名一致[/#c0c0c0]",
            "  [#c0c0c0]description: 描述用途和触发时机[/#c0c0c0]",
            "  [#c0c0c0]---[/#c0c0c0]",
            "  [#c0c0c0]具体的操作步骤和指南...[/#c0c0c0]\n",
            "[bold #4d96ff]Front Matter 字段（agentskills.io 规范）[/bold #4d96ff]",
            "  [#ffd93d]name[/#ffd93d]（必填）小写+连字符，最多 64 字符",
            "  [#ffd93d]description[/#ffd93d]（必填）用途+触发时机，最多 1024 字符",
            "  [#ffd93d]license[/#ffd93d]（可选）许可证（如 Apache-2.0）",
            "  [#ffd93d]compatibility[/#ffd93d]（可选）环境要求，最多 500 字符",
            "  [#ffd93d]metadata[/#ffd93d]（可选）自定义键值对（author/version 等）",
            "  [#ffd93d]allowed-tools[/#ffd93d]（可选）预授权工具列表（实验性）",
            "  [dim #6b7394]nb_agent 扩展字段:[/dim #6b7394]",
            "  [#ffd93d]paths[/#ffd93d]（可选）文件路径 glob 匹配模式",
            "  [#ffd93d]disable-model-invocation[/#ffd93d]（可选）true = 仅手动\n",
            "[bold #4d96ff]Skill 来源[/bold #4d96ff]",
            "  [#6bcb77]●[/#6bcb77] 内置：nb_agent/skills/builtin/",
            "  [#4d96ff]●[/#4d96ff] 全局：~/.nb_agent/skills/ 或 ~/.agents/skills/",
            "  [#b39ddb]●[/#b39ddb] 项目：<项目>/.nb_agent/skills/\n",
            "[dim #6b7394]规范详情: agentskills.io/specification[/dim #6b7394]",
            "[dim #6b7394]按 Esc / Enter 返回[/dim #6b7394]",
        ]
        return "\n".join(lines)

    def action_dismiss_modal(self):
        self.dismiss()


class SkillContentScreen(ModalScreen):
    """Skill 内容详情弹窗"""

    BINDINGS = [
        Binding("escape", "dismiss_modal", "返回"),
        Binding("enter", "dismiss_modal", "返回"),
    ]

    def __init__(self, skill_data: dict, **kwargs):
        super().__init__(**kwargs)
        self.skill_data = skill_data

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="skill-content-dialog"):
            yield Static(self._build_content(), id="skill-content-text")

    def _build_content(self) -> str:
        d = self.skill_data
        lines = []
        lines.append(f"[bold #a78bfa]═══ Skill: {d.get('name', '?')} ═══[/bold #a78bfa]\n")
        lines.append(f"  [#ffd93d]来源:[/#ffd93d] {d.get('source', '?')}")
        lines.append(f"  [#ffd93d]路径:[/#ffd93d] {d.get('skill_path', '?')}")

        paths = d.get("paths", [])
        if paths:
            lines.append(f"  [#ffd93d]匹配:[/#ffd93d] {', '.join(paths)}")

        lines.append("")
        lines.append("[bold #4d96ff]── 内容 ──[/bold #4d96ff]\n")
        content = d.get("content", "无内容")
        for line in content.split("\n"):
            safe = line.replace("[", "\\[")
            lines.append(f"[#c0c0c0]{safe}[/#c0c0c0]")

        lines.append("\n[dim #6b7394]按 Esc / Enter 关闭[/dim #6b7394]")
        return "\n".join(lines)

    def action_dismiss_modal(self):
        self.dismiss()


class MentionSelectScreen(ModalScreen[str]):
    """@ 补全弹窗：搜索并选择工具或 Skill"""

    BINDINGS = [
        Binding("escape", "dismiss_modal", "返回"),
    ]

    def __init__(self, candidates: list, **kwargs):
        super().__init__(**kwargs)
        self.candidates = candidates

    def compose(self) -> ComposeResult:
        with Vertical(id="mention-dialog"):
            yield Static("[bold]@ 引用工具或 Skill[/bold]  (输入过滤, Enter 选择, Esc 返回)", id="mention-title")
            yield Input(placeholder="搜索...", id="mention-filter")
            yield OptionList(id="mention-list")

    def on_mount(self):
        self._render_list("")
        self.query_one("#mention-filter", Input).focus()

    def on_input_changed(self, event: Input.Changed):
        if event.input.id == "mention-filter":
            self._render_list(event.value)

    def _render_list(self, query: str):
        option_list = self.query_one("#mention-list", OptionList)
        option_list.clear_options()
        q = query.lower()

        tools = [c for c in self.candidates if c.get("type") != "skill"]
        skills = [c for c in self.candidates if c.get("type") == "skill"]

        filtered_tools = [c for c in tools if not q or q in c["name"].lower() or q in c.get("description", "").lower()]
        filtered_skills = [c for c in skills if not q or q in c["name"].lower() or q in c.get("description", "").lower()]

        if filtered_tools:
            last_group = None
            for c in filtered_tools:
                group = c.get("group", "")
                if group != last_group:
                    src = c.get("source", "")
                    if src.startswith("MCP:"):
                        option_list.add_option(Option(Text(f"── {group} ──", style="dim #b39ddb"), disabled=True))
                    elif src == "第三方" and group:
                        option_list.add_option(Option(Text(f"── {group} ──", style="dim #4d96ff"), disabled=True))
                    elif group:
                        option_list.add_option(Option(Text(f"── {group} ──", style="dim #6bcb77"), disabled=True))
                    else:
                        option_list.add_option(Option(Text("── 工具 ──", style="dim #6bcb77"), disabled=True))
                    last_group = group

                name = c["name"]
                func_name = c.get("func_name", name)
                desc = c.get("description", "")
                if len(desc) > 50:
                    desc = desc[:50] + "..."
                source = c.get("source", "")

                if source.startswith("MCP:"):
                    icon, style = "◆", "#b39ddb"
                elif source == "第三方":
                    icon, style = "●", "#4d96ff"
                else:
                    icon, style = "●", "#6bcb77"

                label = Text(f"  {icon} {func_name}  ", style=f"bold {style}")
                label.append(desc, style="#8890a8")
                option_list.add_option(Option(label, id=f"tool:{name}"))

        if filtered_skills:
            if filtered_tools:
                option_list.add_option(Option(Text("", style="dim"), disabled=True))
            option_list.add_option(Option(Text("── Skills ──", style="dim #a78bfa"), disabled=True))
            for c in filtered_skills:
                name = c["name"]
                desc = c.get("description", "")
                if len(desc) > 50:
                    desc = desc[:50] + "..."
                manual = " [仅手动]" if c.get("manual_only") else ""
                label = Text(f"  ★ {name}{manual}  ", style="bold #a78bfa")
                label.append(desc, style="#8890a8")
                option_list.add_option(Option(label, id=f"skill:{name}"))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected):
        if event.option.id:
            self.dismiss(event.option.id)

    def action_dismiss_modal(self):
        self.dismiss("")


class AgentSelectScreen(ModalScreen[str]):
    """Agent 管理弹窗"""

    BINDINGS = [
        Binding("escape", "dismiss_modal", "返回"),
    ]

    def __init__(self, agent: AgentCore, **kwargs):
        super().__init__(**kwargs)
        self.agent = agent

    def compose(self) -> ComposeResult:
        with Vertical(id="preset-dialog"):
            yield Static(
                "[bold #a78bfa]✦ Agent 管理[/bold #a78bfa]  [dim #6b7394]↑↓ 选择 · 按钮操作 · Esc 返回[/dim #6b7394]",
                id="preset-title",
            )
            yield OptionList(id="preset-list")
            with Horizontal(id="preset-buttons"):
                yield Button("查看详情", id="btn-agent-view", variant="default")
                yield Button("编辑", id="btn-agent-edit", variant="warning")
                yield Button("应用", id="btn-agent-apply", variant="success")
                yield Button("复制", id="btn-agent-copy", variant="primary")
                yield Button("新建", id="btn-agent-new", variant="primary")
                yield Button("删除", id="btn-agent-delete", variant="error")

    def on_mount(self):
        self._render_list()
        self.query_one("#preset-list", OptionList).focus()

    def _render_list(self):
        option_list = self.query_one("#preset-list", OptionList)
        option_list.clear_options()
        agents = self.agent.get_agents()
        current_id = self.agent.current_agent_id
        for a in agents:
            aid = a["id"]
            name = a["name"]
            prompt_preview = a.get("system_prompt", "")[:40].replace("\n", " ")
            if len(a.get("system_prompt", "")) > 40:
                prompt_preview += "..."
            builtin_tag = " ⚙" if a.get("is_builtin") else ""
            if aid == current_id:
                label = Text(f"  ✦ ", style="bold #00ff88")
                label.append(name, style="bold #00ff88")
                label.append(f"{builtin_tag}  ", style="bold #00ff88")
                label.append("(当前) ", style="bold #00ff88")
                label.append(prompt_preview, style="#5a8a6a")
            else:
                label = Text(f"    ", style="#e0e0e0")
                label.append(name, style="#e0e0e0")
                label.append(f"{builtin_tag}  ", style="#888888")
                label.append(prompt_preview, style="#6b7394")
            option_list.add_option(Option(label, id=aid))

    def _get_highlighted_agent(self):
        option_list = self.query_one("#preset-list", OptionList)
        idx = option_list.highlighted
        if idx is None:
            return None
        opt = option_list.get_option_at_index(idx)
        if not opt.id:
            return None
        for a in self.agent.get_agents():
            if a["id"] == opt.id:
                return a
        return None

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn-agent-view":
            agent_data = self._get_highlighted_agent()
            if agent_data:
                self.app.push_screen(AgentContentScreen(agent_data, self.agent))
            else:
                self.app.notify("请先选中一个 Agent", severity="warning", timeout=2)

        elif event.button.id == "btn-agent-edit":
            agent_data = self._get_highlighted_agent()
            if not agent_data:
                self.app.notify("请先选中一个 Agent", severity="warning", timeout=2)
            elif agent_data.get("is_builtin"):
                self.app.notify("内置 Agent 不可编辑，请先复制", severity="warning", timeout=2)
            else:
                self.dismiss(f"__edit__:{agent_data['id']}")

        elif event.button.id == "btn-agent-apply":
            agent_data = self._get_highlighted_agent()
            if agent_data:
                self.dismiss(agent_data["id"])
            else:
                self.app.notify("请先选中一个 Agent", severity="warning", timeout=2)

        elif event.button.id == "btn-agent-copy":
            agent_data = self._get_highlighted_agent()
            if agent_data:
                self.dismiss(f"__copy__:{agent_data['id']}")
            else:
                self.app.notify("请先选中一个 Agent", severity="warning", timeout=2)

        elif event.button.id == "btn-agent-new":
            self.dismiss("__new__")

        elif event.button.id == "btn-agent-delete":
            self._do_delete()

        self.query_one("#preset-list", OptionList).focus()

    def _do_delete(self):
        option_list = self.query_one("#preset-list", OptionList)
        idx = option_list.highlighted
        if idx is None:
            return
        opt = option_list.get_option_at_index(idx)
        if not opt.id or opt.id == self.agent.DEFAULT_AGENT_ID:
            self.app.notify("默认 Agent 不可删除", severity="warning", timeout=2)
            return
        agent_data = self._get_highlighted_agent()
        if agent_data and agent_data.get("is_builtin"):
            self.app.notify("内置 Agent 不可删除", severity="warning", timeout=2)
            return
        self.agent.delete_agent(opt.id)
        self._render_list()
        self.app.notify("已删除 Agent", timeout=2)

    def action_dismiss_modal(self):
        self.dismiss("")


class AgentContentScreen(ModalScreen):
    """Agent 详情查看弹窗 — 含 system prompt + 工具 + MCP + Skills"""

    BINDINGS = [
        Binding("escape", "dismiss_modal", "返回"),
        Binding("enter", "dismiss_modal", "返回"),
    ]

    def __init__(self, agent_data: dict, agent_core: AgentCore = None, **kwargs):
        super().__init__(**kwargs)
        self.agent_data = agent_data
        self.agent_core = agent_core

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="preset-content-dialog"):
            yield Static(self._build_content(), id="preset-content-text")

    def _build_content(self) -> str:
        a = self.agent_data
        lines = []
        lines.append(f"[bold #a78bfa]═══ Agent: {a.get('name', '?')} ═══[/bold #a78bfa]\n")
        if a.get("is_builtin"):
            lines.append("  [#ffd93d]类型:[/#ffd93d] 内置（不可编辑/删除，可复制）")
        else:
            lines.append(f"  [#ffd93d]ID:[/#ffd93d] {a.get('id', '?')}")

        raw_ag = a.get("allowed_tool_groups")
        ag = set(raw_ag) if raw_ag is not None else None
        raw_as = a.get("allowed_mcp_servers")
        as_ = set(raw_as) if raw_as is not None else None

        lines.append("")
        lines.append("[bold #4d96ff]── System Prompt ──[/bold #4d96ff]\n")
        content = a.get("system_prompt", "无内容")
        for line in content.split("\n"):
            safe = line.replace("[", "\\[")
            lines.append(f"[#c0c0c0]{safe}[/#c0c0c0]")

        default_model = a.get("default_model", "")
        if default_model:
            lines.append("")
            lines.append(f"[bold #4d96ff]── 默认模型 ──[/bold #4d96ff]\n")
            lines.append(f"  [bold #00d4aa]{default_model}[/bold #00d4aa]")

        if self.agent_core:
            lines.append("")
            lines.append("[bold #6bcb77]── 工具/函数 ──[/bold #6bcb77]\n")
            groups = self.agent_core.get_tool_groups()
            non_mcp = [g for g in groups if not g["name"].startswith("mcp__") and g["name"] != "(无分组)"]
            if non_mcp:
                for g in non_mcp:
                    is_allowed = ag is None or g["name"] in ag
                    dot = "[#6bcb77]●[/#6bcb77]" if is_allowed else "[#ffd93d]○[/#ffd93d]"
                    state = "[#6bcb77]启用[/#6bcb77]" if is_allowed else "[#ffd93d]未选中[/#ffd93d]"
                    safe_name = g["name"].replace("[", "\\[")
                    lines.append(f"  {dot} {safe_name} ({g['count']} 个函数) — {state}")
            else:
                lines.append("  [dim #6b7394]无工具组[/dim #6b7394]")

            lines.append("")
            lines.append("[bold #b39ddb]── MCP 服务 ──[/bold #b39ddb]\n")
            servers = self.agent_core.get_mcp_status()
            if servers:
                for s in servers:
                    is_allowed = as_ is None or s["name"] in as_
                    dot = "[#b39ddb]◆[/#b39ddb]" if is_allowed else "[#ffd93d]○[/#ffd93d]"
                    state = "[#b39ddb]启用[/#b39ddb]" if is_allowed else "[#ffd93d]未选中[/#ffd93d]"
                    tc = f" ({s.get('tool_count', 0)} 个工具)" if s.get("tool_count") else ""
                    lines.append(f"  {dot} {s['name']}{tc} — {state}")
            else:
                lines.append("  [dim #6b7394]无 MCP 服务[/dim #6b7394]")

            all_skills = self.agent_core.skill_manager.get_all_skills()
            if all_skills:
                raw_sk = a.get("allowed_skills")
                sk_set = set(raw_sk) if raw_sk is not None else None
                lines.append("")
                lines.append("[bold #ffa726]── Skills ──[/bold #ffa726]\n")
                for sk in all_skills:
                    safe_name = sk["name"].replace("[", "\\[")
                    safe_desc = sk.get("description", "").replace("[", "\\[")
                    is_allowed = sk_set is None or sk["name"] in sk_set
                    if is_allowed:
                        lines.append(f"  [#ffa726]★[/#ffa726] {safe_name} — [dim]{safe_desc}[/dim]")
                    else:
                        lines.append(f"  [#ffd93d]☆[/#ffd93d] [#8890a8]{safe_name} — {safe_desc}[/#8890a8]  [#ffd93d]未选中[/#ffd93d]")

        lines.append("\n[dim #6b7394]按 Esc / Enter 返回[/dim #6b7394]")
        return "\n".join(lines)

    def action_dismiss_modal(self):
        self.dismiss()


class AgentEditScreen(ModalScreen[str]):
    """新建/编辑 Agent 弹窗（含工具组和 MCP 勾选 + 默认模型选择）"""

    BINDINGS = [
        Binding("escape", "cancel", "取消"),
    ]

    def __init__(self, agent_core: AgentCore, edit_agent: dict = None, **kwargs):
        super().__init__(**kwargs)
        self.agent_core = agent_core
        self.edit_agent = edit_agent
        self._all_group_names: list = []
        self._all_server_names: list = []
        self._all_skill_names: list = []
        self._selected_model = ""

    def compose(self) -> ComposeResult:
        from textual.widgets._toggle_button import ToggleButton
        ToggleButton.BUTTON_INNER = "✓"

        title = f"编辑 Agent: {self.edit_agent['name']}" if self.edit_agent else "新建 Agent"
        with VerticalScroll(id="preset-save-dialog"):
            yield Static(f"[bold #ffd93d]{title}[/bold #ffd93d]", id="preset-save-title")
            yield Static("[#c0c0c0]Agent 名称:[/#c0c0c0]")
            yield Input(
                value=self.edit_agent["name"] if self.edit_agent else "",
                placeholder="如：代码审查专家",
                id="agent-name-input",
            )
            yield Static("[#c0c0c0]默认模型 [dim](↑↓ 选择)[/dim]:[/#c0c0c0]")
            yield OptionList(id="agent-model-select")
            yield Static("[#c0c0c0]System Prompt:[/#c0c0c0]")
            from textual.widgets import TextArea
            prompt = self.edit_agent["system_prompt"] if self.edit_agent else ""
            yield TextArea(prompt, id="agent-prompt-input")
            yield Static("[#c0c0c0]工具组 [dim](✓ 启用)[/dim]:[/#c0c0c0]")
            yield self._build_groups_list()
            with Horizontal(classes="agent-toggle-buttons"):
                yield Button("全部启用", id="btn-groups-all", variant="default")
                yield Button("全部禁用", id="btn-groups-none", variant="default")
            yield Static("[#c0c0c0]MCP 服务 [dim](✓ 启用)[/dim]:[/#c0c0c0]")
            yield self._build_servers_list()
            with Horizontal(classes="agent-toggle-buttons"):
                yield Button("全部启用", id="btn-servers-all", variant="default")
                yield Button("全部禁用", id="btn-servers-none", variant="default")
            yield Static("[#c0c0c0]Skills [dim](✓ 注入到 AI 上下文)[/dim]:[/#c0c0c0]")
            yield self._build_skills_list()
            with Horizontal(classes="agent-toggle-buttons"):
                yield Button("全部启用", id="btn-skills-all", variant="default")
                yield Button("全部禁用", id="btn-skills-none", variant="default")
            with Horizontal(id="preset-save-buttons"):
                yield Button("保存", id="btn-save-agent", variant="success")
                yield Button("取消", id="btn-cancel-agent", variant="default")

    def _build_groups_list(self):
        from textual.widgets import SelectionList
        from textual.widgets.selection_list import Selection
        raw = self.edit_agent.get("allowed_tool_groups") if self.edit_agent else None
        allowed = set(raw) if raw is not None else (set() if not self.edit_agent else None)
        groups = self.agent_core.get_tool_groups()
        non_mcp = [g for g in groups if not g["name"].startswith("mcp__") and g["name"] != "(无分组)"]
        selections = []
        for g in non_mcp:
            self._all_group_names.append(g["name"])
            checked = allowed is None or g["name"] in allowed
            selections.append(Selection(f"{g['name']} ({g['count']} 个函数)", g["name"], checked))
        if not selections:
            return Static("[dim #6b7394]无可用工具组[/dim #6b7394]", id="agent-groups-select")
        return SelectionList(*selections, id="agent-groups-select")

    def _build_servers_list(self):
        from textual.widgets import SelectionList
        from textual.widgets.selection_list import Selection
        raw = self.edit_agent.get("allowed_mcp_servers") if self.edit_agent else None
        allowed = set(raw) if raw is not None else (set() if not self.edit_agent else None)
        servers = self.agent_core.get_mcp_status()
        selections = []
        for s in servers:
            self._all_server_names.append(s["name"])
            checked = allowed is None or s["name"] in allowed
            label = f"{s['name']}" + (f" ({s['tool_count']} 个工具)" if s.get("tool_count") else "")
            selections.append(Selection(label, s["name"], checked))
        if not selections:
            return Static("[dim #6b7394]无 MCP 服务[/dim #6b7394]", id="agent-servers-select")
        return SelectionList(*selections, id="agent-servers-select")

    def _build_skills_list(self):
        from textual.widgets import SelectionList
        from textual.widgets.selection_list import Selection
        raw = self.edit_agent.get("allowed_skills") if self.edit_agent else None
        allowed = set(raw) if raw is not None else (set() if not self.edit_agent else None)
        all_skills = self.agent_core.skill_manager.get_all_skills()
        selections = []
        for s in all_skills:
            name = s["name"]
            self._all_skill_names.append(name)
            checked = allowed is None or name in allowed
            suffix = " [仅手动]" if s.get("manual_only") else ""
            selections.append(Selection(f"{name}{suffix} — {s['description'][:40]}", name, checked))
        if not selections:
            return Static("[dim #6b7394]无可用 Skills[/dim #6b7394]", id="agent-skills-select")
        return SelectionList(*selections, id="agent-skills-select")

    def on_mount(self):
        self.query_one("#agent-name-input", Input).focus()
        self._refresh_model_list()

    def _refresh_model_list(self):
        """刷新模型列表，选中当前 Agent 的 default_model 或当前模型"""
        option_list = self.query_one("#agent-model-select", OptionList)
        option_list.clear_options()
        grouped = self.agent_core.get_models_grouped()
        edit_model = self.edit_agent.get("default_model", "") if self.edit_agent else ""
        current = edit_model or self.agent_core.get_model_name()
        self._selected_model = current

        for provider_name, models in grouped.items():
            option_list.add_option(Option(
                Text(f"── {provider_name} ──", style="dim #6b7394"), disabled=True
            ))
            for m in models:
                if m.id == current:
                    label = Text(f"  ▶ {m.id} ({m.name})", style="bold #00d4aa")
                else:
                    label = Text(f"    {m.id} ({m.name})", style="#c0c0c0")
                option_list.add_option(Option(label, id=m.id))

    def _toggle_all(self, widget_id: str, all_names: list, select: bool):
        from textual.widgets import SelectionList
        try:
            sl = self.query_one(f"#{widget_id}", SelectionList)
            for name in all_names:
                if select:
                    sl.select(name)
                else:
                    sl.deselect(name)
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn-save-agent":
            self._do_save()
        elif event.button.id == "btn-cancel-agent":
            self.dismiss("")
        elif event.button.id == "btn-groups-all":
            self._toggle_all("agent-groups-select", self._all_group_names, True)
        elif event.button.id == "btn-groups-none":
            self._toggle_all("agent-groups-select", self._all_group_names, False)
        elif event.button.id == "btn-servers-all":
            self._toggle_all("agent-servers-select", self._all_server_names, True)
        elif event.button.id == "btn-servers-none":
            self._toggle_all("agent-servers-select", self._all_server_names, False)
        elif event.button.id == "btn-skills-all":
            self._toggle_all("agent-skills-select", self._all_skill_names, True)
        elif event.button.id == "btn-skills-none":
            self._toggle_all("agent-skills-select", self._all_skill_names, False)

    def _do_save(self):
        import json as _json
        name = self.query_one("#agent-name-input", Input).value.strip()
        if not name:
            self.app.notify("请输入 Agent 名称", severity="warning", timeout=2)
            return
        from textual.widgets import TextArea, SelectionList
        prompt = self.query_one("#agent-prompt-input", TextArea).text.strip()
        if not prompt:
            self.app.notify("请输入 System Prompt", severity="warning", timeout=2)
            return

        allowed_tool_groups = []
        allowed_mcp_servers = []
        allowed_skills = []
        try:
            groups_select = self.query_one("#agent-groups-select", SelectionList)
            allowed_tool_groups = list(groups_select.selected)
        except Exception:
            pass
        try:
            servers_select = self.query_one("#agent-servers-select", SelectionList)
            allowed_mcp_servers = list(servers_select.selected)
        except Exception:
            pass
        try:
            skills_select = self.query_one("#agent-skills-select", SelectionList)
            allowed_skills = list(skills_select.selected)
        except Exception:
            pass

        result = _json.dumps({
            "edit_id": self.edit_agent["id"] if self.edit_agent else "",
            "name": name,
            "system_prompt": prompt,
            "default_model": self._selected_model,
            "allowed_tool_groups": allowed_tool_groups,
            "allowed_mcp_servers": allowed_mcp_servers,
            "allowed_skills": allowed_skills,
        }, ensure_ascii=False)
        self.dismiss(result)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected):
        if event.option.id:
            self._selected_model = event.option.id

    def action_cancel(self):
        self.dismiss("")


class ToolApprovalScreen(ModalScreen[bool]):
    """工具审批弹窗：危险操作需要用户确认后才执行"""

    BINDINGS = [
        Binding("enter", "approve", "确认执行", priority=True),
        Binding("escape", "reject", "拒绝", priority=True),
    ]

    def __init__(self, tool_name: str, tool_args: dict, **kwargs):
        super().__init__(**kwargs)
        self.tool_name = tool_name
        self.tool_args = tool_args

    def compose(self) -> ComposeResult:
        args_str = json.dumps(self.tool_args, ensure_ascii=False, indent=2)
        with Vertical(id="approval-dialog"):
            yield Static("[bold #ff6b6b]⚠ 工具需要确认[/bold #ff6b6b]", id="approval-title")
            yield Static(f"[bold #ffd93d]工具: {self.tool_name}[/bold #ffd93d]", id="approval-tool")
            yield Static(f"[#c0c0c0]参数:[/#c0c0c0]", id="approval-args-label")
            with VerticalScroll(id="approval-args-scroll"):
                yield Static(Text(args_str, style="#e0e0e0"), id="approval-args")
            yield Static(
                "[bold #6bcb77]Enter = 确认执行[/bold #6bcb77]  |  [bold #ff6b6b]Esc = 拒绝[/bold #ff6b6b]",
                id="approval-footer",
            )

    def action_approve(self):
        self.dismiss(True)

    def action_reject(self):
        self.dismiss(False)
