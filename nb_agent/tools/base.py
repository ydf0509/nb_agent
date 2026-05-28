"""
工具注册框架 — 基于 Pydantic + 装饰器自动生成 OpenAI Function Calling Schema

用法:
    from nb_agent.tools import tool

    class MyParams(BaseModel):
        query: str = Field(description="搜索关键词")

    # 无分组
    @tool
    def search(params: MyParams) -> str:
        \"\"\"搜索互联网\"\"\"
        ...

    # 有分组 — 注册名变为 file__read_file
    @tool(group="file")
    def read_file(params: ReadParams) -> str:
        \"\"\"读取文件\"\"\"
        ...
"""

import inspect
from typing import Dict, Callable, Optional, Type, get_type_hints

from pydantic import BaseModel


TOOL_REGISTRY: Dict[str, dict] = {}


def _pydantic_schema_to_openai_params(model_cls: Type[BaseModel]) -> dict:
    """将 Pydantic model 的 JSON Schema 转换为 OpenAI function parameters 格式"""
    raw_schema = model_cls.model_json_schema()

    properties = {}
    required = []

    for name, field_schema in raw_schema.get("properties", {}).items():
        prop = {}
        field_type = field_schema.get("type")
        if field_type:
            prop["type"] = field_type
            if field_type == "array" and "items" in field_schema:
                prop["items"] = field_schema["items"]
        else:
            prop["type"] = "string"

        if "description" in field_schema:
            prop["description"] = field_schema["description"]

        if "anyOf" in field_schema:
            for variant in field_schema["anyOf"]:
                vtype = variant.get("type")
                if vtype and vtype != "null":
                    prop["type"] = vtype
                    if vtype == "array" and "items" in variant:
                        prop["items"] = variant["items"]
                    break

        if "enum" in field_schema:
            prop["enum"] = field_schema["enum"]

        if "default" in field_schema:
            prop["default"] = field_schema["default"]

        properties[name] = prop

    for name in raw_schema.get("required", []):
        required.append(name)

    return {
        "type": "object",
        "properties": properties,
        "required": required,
    }


def _find_model_cls(func: Callable) -> Optional[Type[BaseModel]]:
    """从函数签名中查找 Pydantic BaseModel 参数类型"""
    try:
        hints = get_type_hints(func)
    except Exception:
        hints = {}

    sig = inspect.signature(func)
    for param_name, param in sig.parameters.items():
        annotation = hints.get(param_name, param.annotation)
        if annotation is inspect.Parameter.empty:
            continue
        if isinstance(annotation, type) and issubclass(annotation, BaseModel):
            return annotation
    return None


def _register_tool(func: Callable, group: Optional[str] = None) -> Callable:
    """核心注册逻辑：解析函数签名，生成 schema，写入 TOOL_REGISTRY"""
    model_cls = _find_model_cls(func)
    if model_cls is None:
        raise TypeError(
            f"工具函数 '{func.__name__}' 必须有一个 Pydantic BaseModel 参数。"
            f"示例: def my_tool(params: MyParams) -> str: ..."
        )

    description = (func.__doc__ or "").strip()
    if not description:
        raise ValueError(f"工具函数 '{func.__name__}' 必须有 docstring 作为工具描述")

    openai_params = _pydantic_schema_to_openai_params(model_cls)
    func_name = func.__name__
    tool_name = f"{group}__{func_name}" if group else func_name

    TOOL_REGISTRY[tool_name] = {
        "function": func,
        "model_cls": model_cls,
        "group": group or "",
        "func_name": func_name,
        "schema": {
            "type": "function",
            "function": {
                "name": tool_name,
                "description": description,
                "parameters": openai_params,
            },
        },
    }

    return func


def tool(func=None, *, group=None):
    """装饰器：自动注册工具函数到 TOOL_REGISTRY

    用法:
        @tool                          # 无分组，注册名 = func_name
        @tool(group="file")            # 有分组，注册名 = file__func_name
    """
    if func is not None:
        return _register_tool(func)
    def decorator(fn):
        return _register_tool(fn, group=group)
    return decorator
