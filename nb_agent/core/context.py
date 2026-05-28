"""上下文窗口管理 — token 估算 + 自动裁剪"""

from typing import List


def estimate_tokens(text: str) -> int:
    """粗略估算 token 数（中文约 1.5 字/token，英文约 4 字符/token）"""
    if not text:
        return 0
    cn_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    en_chars = len(text) - cn_chars
    return int(cn_chars / 1.5 + en_chars / 4)


def _estimate_message_tokens(msg: dict) -> int:
    """估算单条消息的总 token（包括 content、reasoning、tool_calls）"""
    total = estimate_tokens(msg.get("content", "") or "")
    total += estimate_tokens(msg.get("reasoning_content", "") or "")
    for tc in msg.get("tool_calls", []):
        func = tc.get("function", {})
        total += estimate_tokens(func.get("name", ""))
        total += estimate_tokens(func.get("arguments", ""))
    return total


def trim_context(messages: List[dict], context_limit: int) -> List[dict]:
    """当消息总 token 超出模型限制时，从最早的非 system 消息开始移除

    注意：此函数会原地修改传入的 messages 列表。
    """
    if not context_limit:
        return messages

    max_tokens = int(context_limit * 0.85)

    total = sum(_estimate_message_tokens(m) for m in messages)

    while total > max_tokens and len(messages) > 2:
        removed = messages.pop(1)
        total -= _estimate_message_tokens(removed)

    return messages
