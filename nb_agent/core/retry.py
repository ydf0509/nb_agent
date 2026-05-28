"""LLM 调用重试 — 指数退避"""

import asyncio
from openai import APITimeoutError, RateLimitError, APIConnectionError


MAX_RETRIES = 3
RETRY_DELAYS = [1, 3, 5]
RETRYABLE_ERRORS = (APITimeoutError, RateLimitError, APIConnectionError, ConnectionError, TimeoutError)


async def call_llm_with_retry(client, **kwargs):
    """带重试的 LLM 调用（超时/限流/网络错误自动重试）"""
    last_error: Exception = RuntimeError("LLM 调用失败（未知错误）")
    for attempt in range(MAX_RETRIES):
        try:
            return await client.chat.completions.create(**kwargs)
        except RETRYABLE_ERRORS as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
                await asyncio.sleep(delay)
    raise last_error
