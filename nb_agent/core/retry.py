"""LLM 调用重试 — 指数退避 + 双日志（摘要 + 原始）"""

import asyncio
import json
import time
from openai import APITimeoutError, RateLimitError, APIConnectionError

from nb_agent.utils.loggers import logger_llm_call, logger_llm_call_raw

MAX_RETRIES = 3
RETRY_DELAYS = [1, 3, 5]
RETRYABLE_ERRORS = (APITimeoutError, RateLimitError, APIConnectionError, ConnectionError, TimeoutError)


def _safe_serialize(obj, max_len=5000):
    """安全序列化，截断过长内容"""
    try:
        s = json.dumps(obj, ensure_ascii=False, default=str)
        if len(s) > max_len:
            return s[:max_len] + f"...(截断，原始长度 {len(s)})"
        return s
    except Exception:
        return str(obj)[:max_len]


def _full_serialize(obj):
    """完整序列化，不截断"""
    try:
        return json.dumps(obj, ensure_ascii=False, default=str, indent=2)
    except Exception:
        return str(obj)


def _extract_request_summary(kwargs: dict) -> dict:
    """提取请求摘要（不含完整 messages 以免日志过大）"""
    summary = {"model": kwargs.get("model", "?")}

    messages = kwargs.get("messages", [])
    summary["message_count"] = len(messages)
    if messages:
        summary["last_message_role"] = messages[-1].get("role", "?")
        last_content = messages[-1].get("content", "")
        if isinstance(last_content, str) and len(last_content) > 200:
            last_content = last_content[:200] + "..."
        summary["last_message_preview"] = last_content

    tools = kwargs.get("tools", [])
    if tools:
        summary["tool_count"] = len(tools)
        summary["tool_names"] = [t.get("function", {}).get("name", "?") for t in tools[:20]]

    summary["stream"] = kwargs.get("stream", False)
    return summary


def _extract_response_summary(resp) -> dict:
    """提取响应摘要"""
    summary = {}
    try:
        choice = resp.choices[0] if resp.choices else None
        if choice:
            msg = choice.message
            summary["finish_reason"] = choice.finish_reason
            if msg.content:
                content = msg.content
                summary["content_length"] = len(content)
                summary["content_preview"] = content[:300] + "..." if len(content) > 300 else content
            if msg.tool_calls:
                summary["tool_calls"] = [
                    {"name": tc.function.name, "args_preview": tc.function.arguments[:200]}
                    for tc in msg.tool_calls
                ]
            reasoning = getattr(msg, "reasoning_content", None)
            if reasoning:
                summary["reasoning_length"] = len(reasoning)

        if resp.usage:
            summary["usage"] = {
                "prompt": resp.usage.prompt_tokens,
                "completion": resp.usage.completion_tokens,
                "total": (resp.usage.prompt_tokens or 0) + (resp.usage.completion_tokens or 0),
            }
    except Exception as e:
        summary["parse_error"] = str(e)
    return summary


async def call_llm_with_retry(client, **kwargs):
    """带重试的 LLM 调用（超时/限流/网络错误自动重试），双日志"""
    last_error: Exception = RuntimeError("LLM 调用失败（未知错误）")
    req_summary = _extract_request_summary(kwargs)

    for attempt in range(MAX_RETRIES):
        t0 = time.monotonic()
        try:
            # 摘要日志
            logger_llm_call.info(f"[LLM请求] attempt={attempt + 1} | {_safe_serialize(req_summary)}\n\n")
            # 原始日志：完整请求体
            logger_llm_call_raw.info(f"[LLM请求-RAW] attempt={attempt + 1}\n{_full_serialize(kwargs)}\n\n")

            result = await client.chat.completions.create(**kwargs)
            elapsed = time.monotonic() - t0

            if not kwargs.get("stream"):
                # 摘要日志
                resp_summary = _extract_response_summary(result)
                logger_llm_call.info(
                    f"[LLM响应] elapsed={elapsed:.2f}s | {_safe_serialize(resp_summary)}\n\n"
                )
                # 原始日志：完整响应
                try:
                    raw_resp = result.model_dump_json(indent=2)
                except Exception:
                    raw_resp = str(result)
                logger_llm_call_raw.info(f"[LLM响应-RAW] elapsed={elapsed:.2f}s\n{raw_resp}\n\n")
            else:
                logger_llm_call.info(f"[LLM流式] stream opened, elapsed={elapsed:.2f}s\n\n")
                logger_llm_call_raw.info(f"[LLM流式-RAW] stream opened, elapsed={elapsed:.2f}s\n\n")

            return result

        except RETRYABLE_ERRORS as e:
            elapsed = time.monotonic() - t0
            last_error = e
            msg = (f"[LLM重试] attempt={attempt + 1} elapsed={elapsed:.2f}s | "
                   f"{type(e).__name__}: {e}\n\n")
            logger_llm_call.warning(msg)
            logger_llm_call_raw.warning(msg)
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
                await asyncio.sleep(delay)

    fail_msg = f"[LLM失败] 已重试{MAX_RETRIES}次 | {type(last_error).__name__}: {last_error}\n\n"
    logger_llm_call.error(fail_msg)
    logger_llm_call_raw.error(fail_msg)
    raise last_error
