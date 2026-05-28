"""TUI 命令面板 Provider"""

from textual.command import Hit, Hits, Provider, DiscoveryHit


class AgentCommands(Provider):
    """命令面板: 提供会话管理、导出、设置等操作"""

    async def discover(self) -> Hits:
        app = self.app
        commands = [
            ("编辑上轮提问", "撤回最后一轮对话，重新编辑", app._edit_last_message),
            ("切换思考显示", "显示或隐藏 AI 的思考过程", app._cmd_toggle_thinking),
            ("查看工具详情", "查看所有工具的完整描述", app._show_tool_details),
            ("复制为 Markdown", "复制对话为 Markdown 到剪贴板", app._cmd_copy_markdown),
            ("导出 Markdown 文件", "将对话导出为 .md 文件", app._cmd_export_markdown),
        ]
        for name, help_text, callback in commands:
            yield DiscoveryHit(name, callback, help=help_text)

    async def search(self, query: str) -> Hits:
        matcher = self.matcher(query)
        app = self.app
        commands = [
            ("编辑上轮提问", "撤回最后一轮，重新编辑", app._edit_last_message),
            ("切换思考显示", "显示或隐藏思考过程", app._cmd_toggle_thinking),
            ("查看工具详情", "查看所有工具的完整描述", app._show_tool_details),
            ("复制为 Markdown", "复制对话为 Markdown 到剪贴板", app._cmd_copy_markdown),
            ("导出 Markdown 文件", "导出为 .md 文件", app._cmd_export_markdown),
        ]
        for name, help_text, callback in commands:
            score = matcher.match(name)
            if score > 0:
                yield Hit(score, matcher.highlight(name), callback, help=help_text)
