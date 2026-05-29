"""
nb_agent 综合示例 — 展示如何将 nb_agent 作为 Python 库导入使用

涵盖:
  1. 配置加载
  2. 自定义工具注册（@tool 装饰器 + register_tool 动态注册）
  3. Skills 系统（发现、查看、清单注入）
  4. 非流式对话（agent.chat）
  5. 流式对话（agent.chat_stream）
  6. 多会话管理（隔离、切换、历史）
  7. MCP 连接（如已配置）

用法:
    pip install -e .                        # 从 nb_agent 项目根目录安装
    export DEEPSEEK_API_KEY="your-key"      # 设置 API Key
    python main.py                          # 运行
"""

import asyncio
import json
from pathlib import Path

from pydantic import BaseModel, Field

from nb_agent.config import load_config
from nb_agent.core import AgentCore
from nb_agent.skills import SkillManager
from nb_agent.tools import tool


# ========================================================================
# 1. 自定义工具 — @tool 装饰器（import 时自动注册到全局 TOOL_REGISTRY）
# ========================================================================

class WeatherParams(BaseModel):
    city: str = Field(description="城市名称，如 '北京'、'上海'")


@tool
def get_weather(params: WeatherParams) -> str:
    """查询指定城市的天气（模拟数据）"""
    mock_data = {
        "北京": {"temp": 28, "weather": "晴", "humidity": 45},
        "上海": {"temp": 32, "weather": "多云", "humidity": 78},
        "深圳": {"temp": 35, "weather": "雷阵雨", "humidity": 85},
    }
    data = mock_data.get(params.city)
    if data:
        return f"{params.city}: {data['weather']}，{data['temp']}°C，湿度 {data['humidity']}%"
    return f"{params.city}: 暂无天气数据"


# ========================================================================
# 2. 自定义工具 — 普通函数（稍后通过 register_tool 动态注册）
# ========================================================================

def search_docs(query: str, top_k: int = 3) -> str:
    """模拟文档搜索"""
    results = [
        {"title": f"文档{i + 1}: 关于{query}的说明", "score": round(0.95 - i * 0.1, 2)}
        for i in range(top_k)
    ]
    return json.dumps(results, ensure_ascii=False)


# ========================================================================
# 辅助函数
# ========================================================================

def print_section(title: str):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def print_tools(agent: AgentCore):
    print("已注册工具:")
    for t in agent.get_tools():
        print(f"  [{t['source']:>6}] {t['name']}: {t['description'][:50]}")


def print_usage(agent: AgentCore, label: str = ""):
    usage = agent.get_token_usage()
    prefix = f"[{label}] " if label else ""
    print(f"  {prefix}Token: prompt={usage['last_prompt']}, "
          f"completion={usage['last_completion']}, "
          f"tools={usage['last_tool_calls']} | 累计={usage['total']}")


# ========================================================================
# 综合演示
# ========================================================================

async def demo_skills():
    """Part 1: Skills 系统（不需要 API Key）"""
    print_section("Part 1: Skills 系统")

    mgr = SkillManager(project_root=Path.cwd())
    mgr.discover()

    print("自动触发的 Skills:")
    for s in mgr.get_manifest():
        print(f"  - {s['name']}: {s['description'][:60]}...")

    print("\n全部 Skills（含手动模式）:")
    for s in mgr.get_all_skills():
        tag = " [仅手动]" if s["manual_only"] else ""
        print(f"  - {s['name']}{tag}")

    result = mgr.view_skill("code-review")
    if result["success"]:
        lines = result["content"].split("\n")[:3]
        print(f"\nview_skill('code-review') 前 3 行:")
        for line in lines:
            print(f"  {line}")


async def demo_chat(agent: AgentCore):
    """Part 2: 非流式对话 + 自动工具调用"""
    print_section("Part 2: 非流式对话")

    response = await agent.chat("现在几点了？北京天气怎么样？")

    print(f"回复: {response.text[:200]}")
    if response.tool_calls:
        print(f"\n工具调用链:")
        for tc in response.tool_calls:
            print(f"  → {tc.name}({tc.args}) [{tc.status}]")
            print(f"    结果: {tc.result[:80]}")
    print_usage(agent, "非流式")


async def demo_stream(agent: AgentCore):
    """Part 3: 流式对话"""
    print_section("Part 3: 流式对话")

    print("👤 帮我算一下 (123 + 456) * 789\n🤖 ", end="", flush=True)
    async for chunk in agent.chat_stream("帮我算一下 (123 + 456) * 789"):
        print(chunk, end="", flush=True)
    print()
    print_usage(agent, "流式")


async def demo_sessions(agent: AgentCore):
    """Part 4: 多会话管理"""
    print_section("Part 4: 多会话管理")

    session1_id = agent.session_id
    print(f"当前会话 ID: {session1_id}")

    agent.clear_history()
    session2_id = agent.session_id
    print(f"新建会话 ID: {session2_id}")
    print(f"会话已隔离: {session1_id != session2_id}")

    sessions = agent.get_session_list(limit=5)
    if sessions:
        print(f"\n最近 {len(sessions)} 个会话:")
        for s in sessions:
            print(f"  {s['id']} | {s['title'][:30]}")


async def demo_model_info(agent: AgentCore):
    """Part 5: 模型和 MCP 信息"""
    print_section("Part 5: 模型 & MCP 状态")

    print(f"当前模型: {agent.get_model_display_name()} ({agent.get_model_name()})")
    print(f"可用模型: {[m.id for m in agent.available_models]}")

    mcp_status = agent.get_mcp_status()
    if mcp_status:
        print(f"\nMCP Servers:")
        for s in mcp_status:
            state = "已连接" if s["connected"] else f"未连接({s['error'] or '已禁用'})"
            print(f"  {s['name']}: {state}, {s['tools_count']} 个工具")
    else:
        print("\nMCP: 未配置（在 config.jsonc 中添加 mcp 配置即可）")


async def main():
    print("nb_agent 综合示例")
    print(f"版本: {__import__('nb_agent').__version__}")
    print("-" * 60)

    # --- Skills（不需要 API Key） ---
    await demo_skills()

    # --- 加载配置、创建 Agent ---
    config = load_config()
    agent = AgentCore(config)

    # 动态注册自定义工具（方式 2）
    agent.register_tool(
        name="search_docs",
        func=search_docs,
        description="搜索知识库文档",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"},
                "top_k": {"type": "integer", "description": "返回数量", "default": 3},
            },
            "required": ["query"],
        },
    )

    print_tools(agent)

    # --- 连接 MCP ---
    await agent.connect_mcp()

    try:
        await demo_model_info(agent)

        # 以下需要有效的 API Key
        if agent.current_model and agent.current_model.api_key:
            await demo_chat(agent)
            await demo_stream(agent)
            await demo_sessions(agent)
        else:
            print_section("跳过对话演示")
            print("未检测到有效的 API Key，跳过对话演示。")
            print("请设置环境变量（如 DEEPSEEK_API_KEY）并在 config.jsonc 中配置 provider。")

    finally:
        await agent.disconnect_mcp()

    print_section("完成")
    print("所有演示已结束。更多用法请参考 nb_agent 的 README.md。")


if __name__ == "__main__":
    asyncio.run(main())
