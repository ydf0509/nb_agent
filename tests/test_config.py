"""测试配置加载"""
import os
import tempfile
from nb_agent.config import load_config


def test_default_config():
    config = load_config()
    assert "agent" in config
    assert "provider" in config
    assert "mcp" in config
    assert config["agent"]["system_prompt"] == "你是一个智能助手。"


def test_config_from_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonc", delete=False, encoding="utf-8") as f:
        f.write('{\n  "agent": { "system_prompt": "test prompt" }\n}')
        path = f.name
    try:
        config = load_config(cli_config_path=path)
        assert config["agent"]["system_prompt"] == "test prompt"
        assert "provider" in config
    finally:
        os.unlink(path)


def test_env_substitution():
    os.environ["_NB_TEST_KEY"] = "test_value"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonc", delete=False, encoding="utf-8") as f:
        f.write('{ "test": "{env:_NB_TEST_KEY}" }')
        path = f.name
    try:
        config = load_config(cli_config_path=path)
        assert config["test"] == "test_value"
    finally:
        os.unlink(path)
        del os.environ["_NB_TEST_KEY"]


if __name__ == "__main__":
    test_default_config()
    test_config_from_file()
    test_env_substitution()
    print("All config tests passed")
