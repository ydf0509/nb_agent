"""内置工具 — 使用 Pydantic + @tool 装饰器自动注册"""

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


class CalculateParams(BaseModel):
    expression: str = Field(description="数学表达式，如 '2+3*4' 或 '(100-20)/8'")


@tool(group="nb_agent_builtin")
def calculate(params: CalculateParams) -> str:
    """计算数学表达式（支持加减乘除、幂运算、取余等）"""
    import ast
    import operator

    _ops = {
        ast.Add: operator.add, ast.Sub: operator.sub,
        ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod,
        ast.Pow: operator.pow, ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def _safe_eval(node):
        if isinstance(node, ast.Expression):
            return _safe_eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _ops:
            left = _safe_eval(node.left)
            right = _safe_eval(node.right)
            if isinstance(node.op, ast.Pow) and right > 1000:
                raise ValueError("指数过大")
            return _ops[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in _ops:
            return _ops[type(node.op)](_safe_eval(node.operand))
        raise ValueError(f"不支持的表达式: {ast.dump(node)}")

    try:
        tree = ast.parse(params.expression.strip(), mode='eval')
        result = _safe_eval(tree)
        return str(result)
    except ZeroDivisionError:
        return "计算错误: 除以零"
    except Exception as e:
        return f"计算错误: {e}"
