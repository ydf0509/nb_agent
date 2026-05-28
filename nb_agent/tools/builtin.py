"""内置工具 — 框架必需的核心工具"""

import datetime

from pydantic import BaseModel, Field

from .base import tool

from zoneinfo import ZoneInfo


class GetCurrentTimeParams(BaseModel):
    timezone: str = Field(default="Asia/Shanghai", description="时区，默认 Asia/Shanghai")


@tool(group="nb_agent_builtin")
def get_current_time(params: GetCurrentTimeParams) -> str:
    """获取当前日期和时间"""
    try:
        tz = ZoneInfo(params.timezone)
    except (KeyError, Exception):
        tz = ZoneInfo("Asia/Shanghai")
    now = datetime.datetime.now(tz)
    return now.strftime(f"%Y-%m-%d %H:%M:%S ({now.strftime('%A')}) [{params.timezone}]")
