"""数据结构 — AgentCore 使用的 dataclass"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class ToolCallRecord:
    """工具调用记录（给 TUI 展示用）"""
    name: str
    args: dict
    result: str = ""
    status: str = "pending"  # pending / running / done / error


@dataclass
class AgentResponse:
    """Agent 的回复"""
    text: str
    reasoning: str = ""
    tool_calls: list = field(default_factory=list)
    token_usage: dict = field(default_factory=dict)


@dataclass
class ModelInfo:
    """模型信息"""
    id: str
    name: str
    provider: str
    provider_name: str
    base_url: str
    api_key: str
    context_limit: int = 0
    output_limit: int = 0
    raw_id: str = ""


def load_models_from_config(config: dict) -> List[ModelInfo]:
    """从 config.jsonc 的 provider 节解析所有模型"""
    models = []
    for provider_id, provider_cfg in config.get("provider", {}).items():
        provider_name = provider_cfg.get("name", provider_id)
        base_url = provider_cfg.get("base_url", "")
        api_key = provider_cfg.get("api_key", "")

        for model_id, model_cfg in provider_cfg.get("models", {}).items():
            limit = model_cfg.get("limit", {})
            models.append(ModelInfo(
                id=model_id,
                name=model_cfg.get("name", model_id),
                provider=provider_id,
                provider_name=provider_name,
                base_url=base_url,
                api_key=api_key,
                context_limit=limit.get("context", 0),
                output_limit=limit.get("output", 0),
                raw_id=model_cfg.get("raw_model", ""),
            ))
    return models
