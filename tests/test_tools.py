"""测试工具注册和执行"""
from nb_agent.tools import TOOL_REGISTRY


def test_tool_registry_has_builtin():
    assert "nb_agent_builtin__get_current_time" in TOOL_REGISTRY
    assert "nb_agent_builtin__calculate" in TOOL_REGISTRY


def test_tool_schema_format():
    for name, info in TOOL_REGISTRY.items():
        assert "function" in info
        assert "schema" in info
        schema = info["schema"]
        assert schema["type"] == "function"
        assert "name" in schema["function"]
        assert "description" in schema["function"]
        assert "parameters" in schema["function"]


def test_calculate():
    calc = TOOL_REGISTRY["nb_agent_builtin__calculate"]
    params = calc["model_cls"](expression="2+3*4")
    result = calc["function"](params)
    assert result == "14"


def test_get_current_time():
    time_tool = TOOL_REGISTRY["nb_agent_builtin__get_current_time"]
    params = time_tool["model_cls"](timezone="UTC")
    result = time_tool["function"](params)
    assert "UTC" in result


if __name__ == "__main__":
    test_tool_registry_has_builtin()
    test_tool_schema_format()
    test_calculate()
    test_get_current_time()
    print("All tool tests passed")
