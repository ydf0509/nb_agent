"""测试 Skills 系统与 AgentCore 的集成"""
from nb_agent.core import AgentCore


def _make_agent():
    return AgentCore({
        "provider": {
            "test": {
                "api_key": "test",
                "base_url": "https://example.com/v1",
                "models": {"test-model": {"name": "Test"}},
            }
        },
        "agent": {"system_prompt": "你是测试助手。"},
    })


def test_system_prompt_includes_skills():
    agent = _make_agent()
    assert "可用 Skills" in agent.system_prompt
    assert "code-review" in agent.system_prompt
    assert "explain-code" in agent.system_prompt
    assert "refactor" in agent.system_prompt
    assert "view_skill" in agent.system_prompt


def test_tools_include_view_skill():
    agent = _make_agent()
    names = [t["name"] for t in agent.get_tools()]
    assert "view_skill" in names


def test_openai_schema_includes_view_skill():
    agent = _make_agent()
    schemas = agent._get_openai_tools()
    names = [s["function"]["name"] for s in schemas]
    assert "view_skill" in names


def test_view_skill_execution():
    import asyncio
    agent = _make_agent()
    result = asyncio.run(agent._execute_tool("view_skill", {"skill_name": "code-review"}))
    assert len(result) > 50
    assert "审查" in result


def test_view_skill_not_found():
    import asyncio
    agent = _make_agent()
    result = asyncio.run(agent._execute_tool("view_skill", {"skill_name": "xxx"}))
    assert "not found" in result


if __name__ == "__main__":
    test_system_prompt_includes_skills()
    test_tools_include_view_skill()
    test_openai_schema_includes_view_skill()
    test_view_skill_execution()
    test_view_skill_not_found()
    print("All skills integration tests passed")
