"""
配置加载器 — JSONC 格式，支持环境变量替换

加载优先级: CLI 参数 > 环境变量 > 项目级 ./config.jsonc > 全局 ~/.nb_agent/config.jsonc > 默认值

支持 {env:VARIABLE_NAME} 语法从环境变量读取值。
缺失的环境变量替换为空字符串。
"""

import copy
import os
import re
from pathlib import Path

import json5
from dotenv import load_dotenv


DEFAULT_CONFIG = {
    "agent": {
        "system_prompt": "你是一个智能助手。",
        "default_model": "",
        "max_context_tokens": 0,
        "streaming": True,
    },
    "provider": {},
    "mcp": {},
    "approval": {
        "dangerous_tools": [],
        "auto_approve": False,
    },
    "session": {
        "db_path": "",
    },
    "ui": {
        "theme": "dark",
        "show_tool_panel": True,
        "show_token_usage": True,
    },
}


def _substitute_env(text: str) -> str:
    """将 {env:VAR_NAME} 替换为对应环境变量值，缺失则替换为空字符串"""
    return re.sub(r"\{env:([^}]+)\}", lambda m: os.environ.get(m.group(1), ""), text)


def _find_config_file(cli_path: str = "") -> str:
    """按优先级查找配置文件"""
    if cli_path:
        return cli_path

    cwd_config = os.path.join(os.getcwd(), "config.jsonc")
    if os.path.isfile(cwd_config):
        return cwd_config

    home_config = os.path.join(Path.home(), ".nb_agent", "config.jsonc")
    if os.path.isfile(home_config):
        return home_config

    return ""


def _deep_merge(base: dict, override: dict) -> dict:
    """深度合并字典，override 覆盖 base"""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(cli_config_path: str = "", dotenv_path: str = "") -> dict:
    """加载配置，返回合并后的配置字典"""
    if dotenv_path:
        load_dotenv(dotenv_path, override=False)
    else:
        load_dotenv(override=False)

    config_path = _find_config_file(cli_config_path)
    if not config_path:
        return copy.deepcopy(DEFAULT_CONFIG)

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            raw = f.read()
    except (FileNotFoundError, PermissionError) as e:
        import logging
        logging.warning(f"配置文件读取失败: {e}，使用默认配置")
        return copy.deepcopy(DEFAULT_CONFIG)

    raw = _substitute_env(raw)
    try:
        user_config = json5.loads(raw)
    except ValueError as e:
        import logging
        logging.warning(f"配置文件解析失败: {e}，使用默认配置")
        return copy.deepcopy(DEFAULT_CONFIG)

    merged = _deep_merge(copy.deepcopy(DEFAULT_CONFIG), user_config)
    merged["_config_path"] = config_path
    merged["_project_root"] = os.path.dirname(os.path.abspath(config_path))

    return merged
