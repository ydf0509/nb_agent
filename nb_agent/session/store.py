"""会话持久化 — SQLModel ORM，默认 SQLite，可切换 PostgreSQL"""

import json
import os
import datetime
from pathlib import Path
from typing import List, Dict, Optional

from sqlmodel import SQLModel, Session, create_engine, select

from .models import ChatSession, Message, AgentConfig


class SessionStore:

    def __init__(self, db_path: str = ""):
        if not db_path:
            db_dir = os.path.join(Path.home(), ".nb_agent")
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, "sessions.db")

        db_path = os.path.expanduser(db_path)
        parent = os.path.dirname(db_path)
        if parent:
            os.makedirs(parent, exist_ok=True)

        if db_path.startswith("postgresql"):
            self._url = db_path
        else:
            self._url = f"sqlite:///{db_path}"

        connect_args = {}
        if self._url.startswith("sqlite"):
            connect_args["check_same_thread"] = False

        self._engine = create_engine(self._url, connect_args=connect_args)
        SQLModel.metadata.create_all(self._engine)

    def _session(self) -> Session:
        return Session(self._engine)

    # ==================== Session ====================

    def create_session(self, session_id: str, title: str = "",
                       model_id: str = "", agent_id: str = "__default__") -> str:
        now = datetime.datetime.now().isoformat()
        with self._session() as s:
            s.add(ChatSession(
                id=session_id, title=title, model_id=model_id,
                agent_id=agent_id, created_at=now, updated_at=now,
            ))
            s.commit()
        return session_id

    def get_session_title(self, session_id: str) -> str:
        with self._session() as s:
            row = s.get(ChatSession, session_id)
            return row.title if row else ""

    def get_session(self, session_id: str) -> Optional[dict]:
        with self._session() as s:
            row = s.get(ChatSession, session_id)
            return row.model_dump() if row else None

    def update_session_title(self, session_id: str, title: str):
        now = datetime.datetime.now().isoformat()
        with self._session() as s:
            row = s.get(ChatSession, session_id)
            if row:
                row.title = title
                row.updated_at = now
                s.add(row)
                s.commit()

    def list_sessions(self, limit: int = 50) -> List[dict]:
        with self._session() as s:
            stmt = select(ChatSession).order_by(ChatSession.updated_at.desc()).limit(limit)
            rows = s.exec(stmt).all()
            return [r.model_dump() for r in rows]

    def save_message(self, session_id: str, role: str, content: str,
                     reasoning: str = "", tool_calls: Optional[list] = None):
        now = datetime.datetime.now().isoformat()
        tc_json = json.dumps(tool_calls or [], ensure_ascii=False)
        with self._session() as s:
            s.add(Message(
                session_id=session_id, role=role, content=content,
                reasoning=reasoning, tool_calls_json=tc_json, created_at=now,
            ))
            row = s.get(ChatSession, session_id)
            if row:
                row.updated_at = now
                s.add(row)
            s.commit()

    def get_messages(self, session_id: str) -> List[Dict]:
        with self._session() as s:
            stmt = (
                select(Message)
                .where(Message.session_id == session_id)
                .order_by(Message.id)
            )
            rows = s.exec(stmt).all()
            return [
                {
                    "role": r.role,
                    "content": r.content,
                    "reasoning": r.reasoning,
                    "tool_calls_json": r.tool_calls_json,
                }
                for r in rows
            ]

    def delete_session(self, session_id: str):
        with self._session() as s:
            stmt = select(Message).where(Message.session_id == session_id)
            for msg in s.exec(stmt).all():
                s.delete(msg)
            row = s.get(ChatSession, session_id)
            if row:
                s.delete(row)
            s.commit()

    # ==================== Agent ====================

    def create_agent(self, agent_id: str, name: str, system_prompt: str,
                     disabled_groups: list = None, disabled_servers: list = None,
                     is_builtin: bool = False) -> str:
        now = datetime.datetime.now().isoformat()
        with self._session() as s:
            s.add(AgentConfig(
                id=agent_id, name=name, system_prompt=system_prompt,
                disabled_groups_json=json.dumps(disabled_groups or []),
                disabled_servers_json=json.dumps(disabled_servers or []),
                is_builtin=is_builtin,
                created_at=now, updated_at=now,
            ))
            s.commit()
        return agent_id

    def list_agents(self) -> List[dict]:
        with self._session() as s:
            stmt = select(AgentConfig).order_by(AgentConfig.created_at)
            rows = s.exec(stmt).all()
            result = []
            for r in rows:
                d = r.model_dump()
                d["disabled_groups"] = json.loads(d.pop("disabled_groups_json"))
                d["disabled_servers"] = json.loads(d.pop("disabled_servers_json"))
                result.append(d)
            return result

    def get_agent(self, agent_id: str) -> Optional[dict]:
        with self._session() as s:
            row = s.get(AgentConfig, agent_id)
            if not row:
                return None
            d = row.model_dump()
            d["disabled_groups"] = json.loads(d.pop("disabled_groups_json"))
            d["disabled_servers"] = json.loads(d.pop("disabled_servers_json"))
            return d

    def update_agent(self, agent_id: str, name: str, system_prompt: str,
                     disabled_groups: list = None, disabled_servers: list = None):
        now = datetime.datetime.now().isoformat()
        with self._session() as s:
            row = s.get(AgentConfig, agent_id)
            if row:
                row.name = name
                row.system_prompt = system_prompt
                row.disabled_groups_json = json.dumps(disabled_groups or [])
                row.disabled_servers_json = json.dumps(disabled_servers or [])
                row.updated_at = now
                s.add(row)
                s.commit()

    def delete_agent(self, agent_id: str):
        with self._session() as s:
            row = s.get(AgentConfig, agent_id)
            if row:
                s.delete(row)
                s.commit()
