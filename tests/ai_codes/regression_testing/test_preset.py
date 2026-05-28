"""回归测试 — Agent (AgentConfig) CRUD + AgentCore agent 接口"""

import os
import tempfile

import pytest
from nb_agent.session.store import SessionStore
from nb_agent.session.models import AgentConfig


@pytest.fixture
def store(tmp_path):
    db_path = str(tmp_path / "test_agent.db")
    return SessionStore(db_path)


class TestAgentStore:
    """SessionStore agent CRUD"""

    def test_create_and_list(self, store: SessionStore):
        aid = store.create_agent("a1", "翻译助手", "你是一个翻译助手。")
        assert aid == "a1"
        agents = store.list_agents()
        assert len(agents) == 1
        assert agents[0]["name"] == "翻译助手"
        assert agents[0]["system_prompt"] == "你是一个翻译助手。"

    def test_create_with_disabled_fields(self, store: SessionStore):
        store.create_agent(
            "a2", "测试", "prompt",
            disabled_groups=["g1", "g2"],
            disabled_servers=["s1"],
        )
        agent = store.get_agent("a2")
        assert agent["disabled_groups"] == ["g1", "g2"]
        assert agent["disabled_servers"] == ["s1"]

    def test_builtin_flag(self, store: SessionStore):
        store.create_agent("b1", "内置", "prompt", is_builtin=True)
        agent = store.get_agent("b1")
        assert agent["is_builtin"] is True

    def test_multiple_agents(self, store: SessionStore):
        store.create_agent("a", "角色A", "内容A")
        store.create_agent("b", "角色B", "内容B")
        store.create_agent("c", "角色C", "内容C")
        agents = store.list_agents()
        assert len(agents) == 3
        names = [a["name"] for a in agents]
        assert "角色A" in names
        assert "角色B" in names
        assert "角色C" in names

    def test_update_agent(self, store: SessionStore):
        store.create_agent("u1", "原名", "原内容")
        store.update_agent("u1", "新名", "新内容",
                           disabled_groups=["grp"], disabled_servers=["srv"])
        agent = store.get_agent("u1")
        assert agent["name"] == "新名"
        assert agent["system_prompt"] == "新内容"
        assert agent["disabled_groups"] == ["grp"]
        assert agent["disabled_servers"] == ["srv"]

    def test_delete_agent(self, store: SessionStore):
        store.create_agent("d1", "待删除", "xxx")
        store.delete_agent("d1")
        agents = store.list_agents()
        assert len(agents) == 0

    def test_delete_nonexistent(self, store: SessionStore):
        store.delete_agent("nonexistent")
        assert store.list_agents() == []

    def test_agent_fields(self, store: SessionStore):
        store.create_agent("f1", "测试", "内容")
        a = store.list_agents()[0]
        assert a["id"] == "f1"
        assert a["name"] == "测试"
        assert a["system_prompt"] == "内容"
        assert a["created_at"] != ""
        assert a["updated_at"] != ""

    def test_session_with_agent_id(self, store: SessionStore):
        sid = store.create_session("s1", title="test", agent_id="my_agent")
        session = store.get_session("s1")
        assert session["agent_id"] == "my_agent"


class TestAgentCoreAgent:
    """AgentCore agent 接口（不实际连接 LLM）"""

    @pytest.fixture
    def agent(self, tmp_path):
        from nb_agent.core.agent import AgentCore
        config = {
            "agent": {
                "system_prompt": "默认 system prompt",
                "default_model": "",
            },
            "models": [
                {
                    "provider": "test",
                    "provider_name": "Test",
                    "base_url": "http://localhost:9999",
                    "api_key": "test",
                    "models": [{"id": "test-model", "name": "Test"}],
                }
            ],
            "session": {"db_path": str(tmp_path / "agent_test.db")},
        }
        return AgentCore(config)

    def test_default_agent_exists(self, agent):
        agents = agent.get_agents()
        assert len(agents) >= 1
        assert agents[0]["id"] == agent.DEFAULT_AGENT_ID
        assert agents[0]["is_builtin"] is True

    def test_builtin_agents_seeded(self, agent):
        agents = agent.get_agents()
        ids = [a["id"] for a in agents]
        assert "_news_search" in ids
        assert "_code_review" in ids
        assert "_translator" in ids
        assert "_writing" in ids

    def test_save_agent(self, agent):
        before_count = len(agent.get_agents())
        aid = agent.save_agent("代码审查", "你是一个代码审查专家。")
        assert aid
        agents = agent.get_agents()
        assert len(agents) == before_count + 1
        saved = [a for a in agents if a["id"] == aid]
        assert len(saved) == 1
        assert saved[0]["name"] == "代码审查"

    def test_save_agent_with_disabled(self, agent):
        aid = agent.save_agent(
            "自定义", "prompt",
            disabled_groups=["g1"], disabled_servers=["s1"],
        )
        agents = agent.get_agents()
        saved = [a for a in agents if a["id"] == aid][0]
        assert saved["disabled_groups"] == ["g1"]
        assert saved["disabled_servers"] == ["s1"]

    def test_apply_agent(self, agent):
        aid = agent.save_agent("翻译", "你是翻译。")
        old_session = agent.session_id
        agent.apply_agent(aid)
        assert agent.current_agent_id == aid
        assert agent.current_agent_name == "翻译"
        assert agent.session_id != old_session
        assert agent.total_prompt_tokens == 0
        assert len(agent.messages) == 1
        assert agent.messages[0]["role"] == "system"

    def test_apply_agent_sets_disabled(self, agent):
        aid = agent.save_agent(
            "受限", "prompt",
            disabled_groups=["g1", "g2"], disabled_servers=["srv"],
        )
        agent.apply_agent(aid)
        assert "g1" in agent.disabled_tool_groups
        assert "g2" in agent.disabled_tool_groups

    def test_apply_resets_tokens(self, agent):
        agent.total_prompt_tokens = 1000
        agent.total_completion_tokens = 500
        agent.apply_agent(agent.DEFAULT_AGENT_ID)
        assert agent.total_prompt_tokens == 0
        assert agent.total_completion_tokens == 0

    def test_delete_agent_basic(self, agent):
        aid = agent.save_agent("临时", "tmp")
        assert agent.delete_agent(aid) is True
        agents = agent.get_agents()
        assert all(a["id"] != aid for a in agents)

    def test_delete_default_blocked(self, agent):
        assert agent.delete_agent(agent.DEFAULT_AGENT_ID) is False

    def test_update_agent_updates_current(self, agent):
        aid = agent.save_agent("原始", "原始内容")
        agent.apply_agent(aid)
        agent.update_agent(aid, "新名", "新内容")
        assert agent.current_agent_name == "新名"
        assert "新内容" in agent.system_prompt

    def test_update_agent_updates_disabled(self, agent):
        aid = agent.save_agent("测试", "prompt")
        agent.apply_agent(aid)
        agent.update_agent(aid, "测试", "prompt",
                           disabled_groups=["grp"], disabled_servers=["srv"])
        assert "grp" in agent.disabled_tool_groups

    def test_delete_current_switches_to_default(self, agent):
        aid = agent.save_agent("当前", "当前内容")
        agent.apply_agent(aid)
        assert agent.current_agent_id == aid
        agent.delete_agent(aid)
        assert agent.current_agent_id == agent.DEFAULT_AGENT_ID

    def test_session_bound_to_agent(self, agent):
        aid = agent.save_agent("绑定", "prompt")
        agent.apply_agent(aid)
        session = agent.session_store.get_session(agent.session_id)
        assert session["agent_id"] == aid
