"""右侧工具/模型/MCP/Token 信息面板"""

from textual.containers import Vertical, VerticalScroll
from textual.app import ComposeResult
from textual.widgets import OptionList, RichLog, Static
from textual.widgets.option_list import Option
from rich.text import Text

from nb_agent.core import AgentCore
from .inputs import ClickableStatic


def _fmt_tokens(n: int) -> str:
    return f"{n / 1000:.1f}k"


class ToolPanel(Vertical):
    """右侧信息面板：分区展示，各区独立滚动"""

    def __init__(self, agent: AgentCore, **kwargs):
        super().__init__(**kwargs)
        self.agent = agent

    def compose(self) -> ComposeResult:
        yield Static("", id="section-tokens")
        yield Static("", id="section-models-title")
        yield OptionList(id="section-models-list")
        yield Static("", id="section-mcp-title")
        yield OptionList(id="section-mcp-list")
        yield Static("", id="section-groups-title")
        yield OptionList(id="section-groups-list")
        yield ClickableStatic("", id="section-tools-title")
        with VerticalScroll(id="section-tools-scroll"):
            yield ClickableStatic("", id="section-tools")

    def on_mount(self):
        self.update_content()

    def update_content(self, last_elapsed: float = 0.0):
        t = self.agent.get_token_usage()
        if t['total'] == 0 and t.get('last_rounds', 0) == 0:
            token_text = "[bold #ffd93d]✦ Token:[/bold #ffd93d] [#6b7394]等待对话...[/#6b7394]"
        else:
            elapsed_str = f" | 耗时{last_elapsed:.1f}s" if last_elapsed > 0 else ""
            last_info = f"本次 {_fmt_tokens(t['last_total'])}(入{_fmt_tokens(t['last_prompt'])}+出{_fmt_tokens(t['last_completion'])}){elapsed_str}"
            total_info = f"累计 {_fmt_tokens(t['total'])}(入{_fmt_tokens(t['total_prompt'])}+出{_fmt_tokens(t['total_completion'])})"
            token_text = (
                f"[bold #ffd93d]✦ Token[/bold #ffd93d]\n"
                f"  [#ffd93d]{last_info}[/#ffd93d]\n"
                f"  [#c0c0c0]{total_info}[/#c0c0c0]"
            )
        self.query_one("#section-tokens", Static).update(token_text)

        current_id = self.agent.get_model_name()
        grouped = self.agent.get_models_grouped()
        total = len(self.agent.available_models)
        self.query_one("#section-models-title", Static).update(
            f"[bold #4d96ff]模型 ({total})[/bold #4d96ff] [#6b7394]点击切换[/#6b7394]"
        )

        option_list = self.query_one("#section-models-list", OptionList)
        option_list.clear_options()
        for provider_name, models in grouped.items():
            option_list.add_option(Option(
                Text(f"── {provider_name} ──", style="#6b7394"), disabled=True
            ))
            for m in models:
                if m.id == current_id:
                    label = Text(f"▶ {m.id}", style="bold #00d4aa")
                else:
                    label = Text(f"  {m.id}", style="#8890a8")
                option_list.add_option(Option(label, id=m.id))

        mcp_status = self.agent.get_mcp_status()
        active_count = sum(1 for s in mcp_status if s["connected"] and not s.get("disabled"))
        self.query_one("#section-mcp-title", Static).update(
            f"[bold #ff922b]MCP Server ({active_count}/{len(mcp_status)})[/bold #ff922b] [#6b7394]点击切换[/#6b7394]"
        )
        mcp_list = self.query_one("#section-mcp-list", OptionList)
        mcp_list.clear_options()
        if not mcp_status:
            mcp_list.add_option(Option(Text("无配置", style="#6b7394"), disabled=True))
        else:
            mcp_sorted = sorted(mcp_status, key=lambda s: (
                s.get("config_disabled", False) or s.get("disabled", False) or not s["connected"],
                s["name"],
            ))
            for s in mcp_sorted:
                name = s["name"]
                if s.get("config_disabled"):
                    label = Text(f"  ○ {name} (配置禁用)", style="#6b7394")
                elif s.get("disabled"):
                    label = Text(f"  ◌ {name} (已禁用 {s['tools_count']}工具)", style="#8890a8")
                elif s["connected"]:
                    label = Text(f"  ● {name} ({s['tools_count']}工具)", style="#6bcb77")
                else:
                    err = s["error"][:20] if s["error"] else "失败"
                    label = Text(f"  ○ {name}: {err}", style="#ff6b6b")
                mcp_list.add_option(Option(label, id=f"mcp__{name}"))

        tool_groups = self.agent.get_tool_groups()
        toggleable = [g for g in tool_groups if g["name"] != "(无分组)" and not g["name"].startswith("mcp__")]
        if toggleable:
            enabled_groups = sum(1 for g in toggleable if not g["disabled"])
            self.query_one("#section-groups-title", Static).update(
                f"[bold #ffd93d]工具分组 ({enabled_groups}/{len(toggleable)})[/bold #ffd93d] [#6b7394]点击切换[/#6b7394]"
            )
            groups_list = self.query_one("#section-groups-list", OptionList)
            groups_list.clear_options()
            toggleable.sort(key=lambda g: (g["disabled"], g["name"]))
            for g in toggleable:
                name = g["name"]
                count = g["count"]
                source = g["source"]
                if g["disabled"]:
                    label = Text(f"  ○ {name} ({count}工具) [已禁用]", style="#ffd93d")
                elif source.startswith("MCP:"):
                    label = Text(f"  ● {name} ({count}工具)", style="#b39ddb")
                elif source == "第三方":
                    label = Text(f"  ● {name} ({count}工具)", style="#4d96ff")
                else:
                    label = Text(f"  ● {name} ({count}工具)", style="#6bcb77")
                groups_list.add_option(Option(label, id=f"group__{name}"))
        else:
            self.query_one("#section-groups-title", Static).update("")
            groups_list = self.query_one("#section-groups-list", OptionList)
            groups_list.clear_options()

        tools = self.agent.get_tools()
        enabled_count = sum(1 for t in tools if not t.get("disabled"))
        self.query_one("#section-tools-title", Static).update(
            f"[bold #6bcb77]函数 ({enabled_count}/{len(tools)})[/bold #6bcb77] [dim #6b7394]点击查看详情[/dim #6b7394]"
        )

        groups = {}
        for t in tools:
            group = t.get("group", "") or "(无分组)"
            if group not in groups:
                groups[group] = {"tools": [], "source": t["source"], "disabled": t.get("disabled", False)}
            groups[group]["tools"].append(t)

        tool_lines = []
        for group_name in sorted(groups.keys(), key=lambda n: (groups[n]["disabled"], n)):
            g = groups[group_name]
            src = g["source"]
            disabled = g["disabled"]
            disabled_tag = " [已禁用]" if disabled else ""
            if disabled:
                tool_lines.append(f"[dim #ffd93d]── {group_name}{disabled_tag} ──[/dim #ffd93d]")
            elif src.startswith("MCP:"):
                tool_lines.append(f"[dim #b39ddb]── {group_name} ──[/dim #b39ddb]")
            elif group_name == "(无分组)":
                tool_lines.append(f"[dim #6b7394]── {group_name} ──[/dim #6b7394]")
            elif src == "第三方":
                tool_lines.append(f"[dim #4d96ff]── {group_name} ──[/dim #4d96ff]")
            else:
                tool_lines.append(f"[dim #6bcb77]── {group_name} ──[/dim #6bcb77]")
            for t in g["tools"]:
                func_name = t.get("func_name", t["name"])
                t_src = t.get("source", "")
                if disabled:
                    tool_lines.append(f"  [#ffd93d]○ {func_name}[/#ffd93d]")
                elif t_src.startswith("MCP:"):
                    tool_lines.append(f"  [#b39ddb]◆[/#b39ddb] [#c0c0c0]{func_name}[/#c0c0c0]")
                elif t_src == "第三方":
                    tool_lines.append(f"  [#4d96ff]●[/#4d96ff] [#c0c0c0]{func_name}[/#c0c0c0]")
                else:
                    tool_lines.append(f"  [#6bcb77]●[/#6bcb77] [#c0c0c0]{func_name}[/#c0c0c0]")
        self.query_one("#section-tools", Static).update("\n".join(tool_lines))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected):
        if not event.option.id:
            return
        opt_id = event.option.id

        if opt_id.startswith("group__"):
            group_name = opt_id[7:]
            enabled = self.agent.toggle_tool_group(group_name)
            state = "启用" if enabled else "禁用"
            chat = self.app.query_one("#chat-panel", RichLog)
            chat.write(f"[#ffd93d]✦ 工具组 [{group_name}] 已{state}[/#ffd93d]")
            self.update_content()
            return

        if opt_id.startswith("mcp__"):
            server_name = opt_id[5:]
            status = self.agent.get_mcp_status()
            srv = next((s for s in status if s["name"] == server_name), None)
            if srv and srv.get("config_disabled"):
                self.app.notify(f"{server_name} 在配置中禁用，请修改 config.jsonc", severity="warning", timeout=3)
                return
            if srv and not srv["connected"]:
                self.app.notify(f"{server_name} 连接失败，无法切换", severity="warning", timeout=3)
                return
            enabled = self.agent.toggle_mcp_server(server_name)
            state = "启用" if enabled else "禁用"
            chat = self.app.query_one("#chat-panel", RichLog)
            chat.write(f"[#ff922b]✦ MCP [{server_name}] 已{state}[/#ff922b]")
            self.update_content()
            return

        model_id = opt_id
        old = self.agent.get_model_name()
        if model_id == old:
            return
        if self.agent.switch_model(model_id):
            chat = self.app.query_one("#chat-panel", RichLog)
            chat.write(f"\n[bold #ffd93d]✦ 模型已切换:[/bold #ffd93d] [#6b7394]{old}[/#6b7394] → [bold #00d4aa]{self.agent.get_model_name()}[/bold #00d4aa]")
            app = self.app
            if hasattr(app, '_update_subtitle'):
                app._update_subtitle()
            self.update_content()
