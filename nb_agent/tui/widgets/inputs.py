"""聊天输入组件"""

from textual import events
from textual.message import Message
from textual.widgets import Static, TextArea


class ChatInput(TextArea):
    """聊天输入框：Enter=换行，Ctrl+J=发送，@=触发补全"""

    class MentionTriggered(Message):
        """输入 @ 时触发，通知 App 打开补全弹窗"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.show_line_numbers = False

    def on_key(self, event: events.Key) -> None:
        if event.character == "@":
            self.set_timer(0.05, self._emit_mention)

    def _emit_mention(self) -> None:
        self.post_message(self.MentionTriggered())


class ClickableStatic(Static):
    """可点击的 Static 组件 — 点击时打开工具详情"""

    def on_click(self, event):
        app = self.app
        if hasattr(app, '_show_tool_details'):
            app._show_tool_details()
