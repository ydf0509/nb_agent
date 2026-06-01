"""SQLModel 数据模型 — 会话、消息、Agent 配置"""

from typing import Optional
from sqlmodel import SQLModel, Field


class ChatSession(SQLModel, table=True):
    __tablename__ = "sessions"

    id: str = Field(primary_key=True)
    title: str = Field(default="")
    model_id: str = Field(default="")
    agent_id: str = Field(default="__default__")
    created_at: str = Field(default="")
    updated_at: str = Field(default="")


class Message(SQLModel, table=True):
    __tablename__ = "messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(index=True)
    role: str = Field(default="")
    content: str = Field(default="")
    reasoning: str = Field(default="")
    tool_calls_json: str = Field(default="[]")
    created_at: str = Field(default="")


class AgentConfig(SQLModel, table=True):
    __tablename__ = "agent_configs"

    id: str = Field(primary_key=True)
    name: str = Field(default="")
    system_prompt: str = Field(default="")
    default_model: str = Field(default="")
    allowed_tool_groups_json: str = Field(default="null")
    allowed_mcp_servers_json: str = Field(default="null")
    allowed_skills_json: str = Field(default="null")
    is_builtin: bool = Field(default=False)
    created_at: str = Field(default="")
    updated_at: str = Field(default="")
