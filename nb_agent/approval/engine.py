"""工具审批规则引擎 — 判断工具调用是否需要用户确认"""

from typing import Callable, List, Optional


ALWAYS_APPROVE_TOOLS = {
    "mcp__dev-toolkit__kill_process",
    "mcp__redis-tools__redis_smart_set",
}

REDIS_WRITE_COMMANDS = {
    "SET", "SETNX", "SETEX", "PSETEX", "MSET", "MSETNX", "APPEND",
    "INCR", "INCRBY", "INCRBYFLOAT", "DECR", "DECRBY",
    "DEL", "UNLINK", "RENAME", "RENAMENX", "EXPIRE", "EXPIREAT",
    "PEXPIRE", "PEXPIREAT", "PERSIST", "MOVE", "COPY",
    "HSET", "HSETNX", "HMSET", "HDEL", "HINCRBY", "HINCRBYFLOAT",
    "LPUSH", "RPUSH", "LPOP", "RPOP", "LSET", "LINSERT", "LREM", "LTRIM",
    "SADD", "SREM", "SPOP", "SMOVE", "SDIFFSTORE", "SINTERSTORE", "SUNIONSTORE",
    "ZADD", "ZREM", "ZINCRBY", "ZPOPMIN", "ZPOPMAX",
    "XADD", "XDEL", "XTRIM",
    "PFADD", "PFMERGE",
    "GEOADD",
}


def rule_redis_write(tool_name: str, tool_kwargs: dict) -> bool:
    """redis_execute 中的写命令需要审批"""
    if tool_name != "mcp__redis-tools__redis_execute":
        return False
    cmd_parts = tool_kwargs.get("command", "").strip().split()
    if not cmd_parts:
        return False
    return cmd_parts[0].upper() in REDIS_WRITE_COMMANDS


def rule_dangerous_tools(tool_name: str, tool_kwargs: dict) -> bool:
    """ALWAYS_APPROVE_TOOLS 名单中的工具始终需要审批"""
    return tool_name in ALWAYS_APPROVE_TOOLS


DEFAULT_RULES: List[Callable[[str, dict], bool]] = [
    rule_redis_write,
    rule_dangerous_tools,
]


class ApprovalEngine:
    """工具审批规则引擎：可插拔规则列表，任一命中即触发审批"""

    def __init__(self, rules: Optional[List[Callable]] = None,
                 extra_dangerous: Optional[List[str]] = None):
        self.rules: List[Callable] = list(rules or DEFAULT_RULES)
        if extra_dangerous:
            extra_set = set(extra_dangerous)
            self.rules.append(lambda name, kwargs: name in extra_set)

    def needs_approval(self, tool_name: str, tool_kwargs: dict) -> bool:
        return any(rule(tool_name, tool_kwargs) for rule in self.rules)

    def add_rule(self, rule: Callable):
        self.rules.append(rule)

    def remove_rule(self, rule: Callable):
        self.rules = [r for r in self.rules if r is not rule]
