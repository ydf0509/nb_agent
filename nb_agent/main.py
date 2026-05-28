"""nb_agent CLI 入口"""

import argparse
import os
import sys


def main():
    parser = argparse.ArgumentParser(description="nb_agent — Handwritten ReAct Agent with TUI")
    parser.add_argument("--config", "-c", help="配置文件路径 (JSONC)")
    parser.add_argument("--dotenv", help=".env 文件路径")

    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="非交互模式：执行一次对话")
    run_parser.add_argument("prompt", nargs="?", help="用户提问")
    run_parser.add_argument("-f", "--file", help="从文件读取 prompt")

    subparsers.add_parser("sessions", help="会话管理")

    args = parser.parse_args()

    from nb_agent.config import load_config
    config = load_config(
        cli_config_path=args.config or "",
        dotenv_path=args.dotenv or "",
    )
    config["_project_root"] = os.getcwd()

    if args.command == "run":
        _run_once(config, args)
    elif args.command == "sessions":
        _list_sessions(config)
    else:
        _run_tui(config)


def _run_tui(config: dict):
    try:
        from nb_agent.tui.app import AgentApp
    except ImportError:
        print("TUI 依赖未安装，请运行: pip install nb_agent[tui]")
        sys.exit(1)
    app = AgentApp(config)
    app.run()


def _run_once(config: dict, args):
    import asyncio

    prompt = args.prompt or ""
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            prompt = f.read()
    if not prompt:
        print("错误：请提供 prompt 或 -f 文件")
        sys.exit(1)

    from nb_agent.core import AgentCore

    async def _run():
        agent = AgentCore(config)
        await agent.connect_mcp()
        try:
            async for chunk in agent.chat_stream(prompt):
                print(chunk, end="", flush=True)
            print()
        finally:
            await agent.disconnect_mcp()

    asyncio.run(_run())


def _list_sessions(config: dict):
    from nb_agent.session import SessionStore
    db_path = config.get("session", {}).get("db_path", "")
    store = SessionStore(db_path)
    sessions = store.list_sessions(limit=20)
    if not sessions:
        print("暂无历史会话")
        return
    for s in sessions:
        print(f"  {s['id']}  {s['title'][:40]:<40}  {s['updated_at'][:19]}")


if __name__ == "__main__":
    main()
