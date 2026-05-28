"""工具审批规则引擎 — 判断工具调用是否需要用户确认

使用方式:
    engine = ApprovalEngine()
    engine.add_rule(my_rule_func)  # 添加自定义规则

    if engine.needs_approval("tool_name", {"arg": "value"}):
        # 弹窗让用户确认
        ...

规则函数签名: (tool_name: str, tool_kwargs: dict) -> bool
    返回 True 表示需要审批，False 表示放行。
"""

from typing import Callable, List, Optional


class ApprovalEngine:
    """工具审批规则引擎：可插拔规则列表，任一命中即触发审批弹窗"""

    def __init__(self, rules: Optional[List[Callable]] = None,
                 extra_dangerous: Optional[List[str]] = None):
        self.rules: List[Callable] = list(rules or [])
        if extra_dangerous:
            extra_set = set(extra_dangerous)
            self.rules.append(lambda name, kwargs: name in extra_set)

    def needs_approval(self, tool_name: str, tool_kwargs: dict) -> bool:
        return any(rule(tool_name, tool_kwargs) for rule in self.rules)

    def add_rule(self, rule: Callable):
        self.rules.append(rule)

    def remove_rule(self, rule: Callable):
        self.rules = [r for r in self.rules if r is not rule]
