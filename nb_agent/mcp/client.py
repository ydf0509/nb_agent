"""
MCP 客户端管理器 — 连接多个 MCP Server，统一管理工具

支持三种传输方式:
  - local (stdio): 启动子进程，通过 stdin/stdout 通信
  - sse: 通过 SSE 连接远程 MCP Server
  - streamableHttp: 通过 Streamable HTTP 连接远程 MCP Server
"""

import asyncio
import contextlib
import json
import os
import sys
from typing import Dict, List, Optional, Any, TextIO

from nb_agent.utils.loggers import logger_mcp

try:
    from mcp import ClientSession
    from mcp.client.stdio import stdio_client, StdioServerParameters
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logger_mcp.warning("MCP SDK 未安装，请运行: pip install mcp")

try:
    from mcp.client.sse import sse_client
    SSE_AVAILABLE = True
except ImportError:
    SSE_AVAILABLE = False

try:
    from mcp.client.streamable_http import streamablehttp_client
    STREAMABLE_HTTP_AVAILABLE = True
except ImportError:
    STREAMABLE_HTTP_AVAILABLE = False


class MCPServerInfo:
    """单个 MCP Server 的连接信息"""

    def __init__(self, name: str, session=None):
        self.name = name
        self.session = session
        self.tools: list = []
        self.connected = False
        self.error = ""
        self._exit_stack: Optional[contextlib.AsyncExitStack] = None


class MCPManager:
    """管理多个 MCP Server 的连接和工具调用"""

    def __init__(self):
        self.servers: Dict[str, MCPServerInfo] = {}
        self._stdio_exit_stack = contextlib.AsyncExitStack()
        self._project_root = ""
        self._all_configs: Dict[str, dict] = {}
        self._allowed_servers: set = None
        self.errlog: Optional[TextIO] = None

    async def connect_all(self, mcp_config: dict, project_root: str = ""):
        """根据配置连接所有 MCP Server

        SSE/HTTP 连接必须在调用者任务中初始化（anyio cancel scope 要求），
        因此只有 stdio 类型才能用 asyncio.gather 并发启动。
        """
        self._project_root = project_root
        self._all_configs = dict(mcp_config)

        if not MCP_AVAILABLE:
            logger_mcp.error("MCP SDK 未安装，跳过所有 MCP 连接")
            return

        stdio_tasks = []
        remote_servers = []

        for name, cfg in mcp_config.items():
            if not cfg.get("enabled", True):
                continue
            server_type = cfg.get("type", "local")
            if server_type in ("sse", "streamableHttp", "streamable_http"):
                remote_servers.append((name, cfg))
            else:
                stdio_tasks.append(self.connect_server(name, cfg))

        if stdio_tasks:
            await asyncio.gather(*stdio_tasks, return_exceptions=True)

        for name, cfg in remote_servers:
            await self.connect_server(name, cfg)

    async def connect_server(self, name: str, cfg: dict):
        """连接单个 MCP Server"""
        if not MCP_AVAILABLE:
            return

        info = MCPServerInfo(name)
        self.servers[name] = info
        server_type = cfg.get("type", "local")

        try:
            if server_type in ("sse",):
                await self._connect_sse(name, cfg, info)
            elif server_type in ("streamableHttp", "streamable_http"):
                await self._connect_streamable_http(name, cfg, info)
            else:
                await self._connect_stdio(name, cfg, info)

            logger_mcp.info(f"MCP [{name}] 已连接 ({server_type})，{len(info.tools)} 个工具")

        except asyncio.TimeoutError:
            info.error = "连接超时"
            logger_mcp.error(f"MCP [{name}] 连接超时")
            await self._cleanup_remote(info)
        except FileNotFoundError as e:
            info.error = f"命令未找到: {e}"
            logger_mcp.error(f"MCP [{name}] {info.error}")
        except BaseException as e:
            if isinstance(e, BaseExceptionGroup):
                msgs = [f"{type(se).__name__}: {se}" for se in e.exceptions]
                info.error = "; ".join(msgs)
            else:
                info.error = f"{type(e).__name__}: {e}"
            logger_mcp.error(f"MCP [{name}] 连接失败: {info.error}")
            await self._cleanup_remote(info)

    @staticmethod
    async def _cleanup_remote(info: MCPServerInfo):
        if info._exit_stack is not None:
            try:
                await info._exit_stack.aclose()
            except (Exception, BaseException):
                pass
            info._exit_stack = None

    async def _connect_stdio(self, name: str, cfg: dict, info: MCPServerInfo):
        command = cfg.get("command", [])
        if isinstance(command, str):
            command = [command]
        args = cfg.get("args", [])
        full_command = command + args
        if not full_command:
            info.error = "未配置 command"
            return

        custom_env = cfg.get("environment", {})
        merged_env = {**os.environ, **custom_env} if custom_env else None
        cwd = cfg.get("cwd", self._project_root or None)

        server_params = StdioServerParameters(
            command=full_command[0],
            args=full_command[1:] if len(full_command) > 1 else [],
            env=merged_env,
            cwd=cwd,
        )

        errlog = self.errlog if self.errlog and not self.errlog.closed else sys.stderr
        transport = stdio_client(server_params, errlog=errlog)
        streams = await self._stdio_exit_stack.enter_async_context(transport)
        session = ClientSession(*streams)
        await self._stdio_exit_stack.enter_async_context(session)

        init_timeout = cfg.get("init_timeout", 60)
        await asyncio.wait_for(session.initialize(), timeout=init_timeout)

        tools_result = await asyncio.wait_for(session.list_tools(), timeout=30)
        info.session = session
        info.tools = tools_result.tools if tools_result.tools else []
        info.connected = True

    async def _connect_sse(self, name: str, cfg: dict, info: MCPServerInfo):
        if not SSE_AVAILABLE:
            info.error = "mcp SSE 客户端不可用，请升级: pip install mcp[sse]"
            return

        url = cfg.get("url", "")
        if not url:
            info.error = "SSE 类型需要配置 url"
            return

        headers = cfg.get("headers", {})
        exit_stack = contextlib.AsyncExitStack()
        info._exit_stack = exit_stack

        transport = sse_client(url=url, headers=headers)
        streams = await exit_stack.enter_async_context(transport)
        session = ClientSession(*streams)
        await exit_stack.enter_async_context(session)

        init_timeout = cfg.get("init_timeout", 30)
        await asyncio.wait_for(session.initialize(), timeout=init_timeout)

        tools_result = await asyncio.wait_for(session.list_tools(), timeout=30)
        info.session = session
        info.tools = tools_result.tools if tools_result.tools else []
        info.connected = True

    async def _connect_streamable_http(self, name: str, cfg: dict, info: MCPServerInfo):
        if not STREAMABLE_HTTP_AVAILABLE:
            info.error = "mcp Streamable HTTP 客户端不可用，请升级: pip install mcp"
            return

        url = cfg.get("url", "") or cfg.get("baseUrl", "")
        if not url:
            info.error = "streamableHttp 类型需要配置 url 或 baseUrl"
            return

        headers = cfg.get("headers", {})
        exit_stack = contextlib.AsyncExitStack()
        info._exit_stack = exit_stack

        transport = streamablehttp_client(url=url, headers=headers)
        streams = await exit_stack.enter_async_context(transport)
        read_stream, write_stream = streams[0], streams[1]
        session = ClientSession(read_stream, write_stream)
        await exit_stack.enter_async_context(session)

        init_timeout = cfg.get("init_timeout", 30)
        await asyncio.wait_for(session.initialize(), timeout=init_timeout)

        tools_result = await asyncio.wait_for(session.list_tools(), timeout=30)
        info.session = session
        info.tools = tools_result.tools if tools_result.tools else []
        info.connected = True

    async def disconnect_all(self):
        try:
            await self._stdio_exit_stack.aclose()
        except (Exception, BaseException):
            pass
        self._stdio_exit_stack = contextlib.AsyncExitStack()

        for info in self.servers.values():
            if info._exit_stack is not None:
                try:
                    await info._exit_stack.aclose()
                except (Exception, BaseException):
                    pass
                info._exit_stack = None

        self.servers.clear()

    def toggle_server(self, name: str) -> bool:
        """切换 MCP Server 启用/禁用，返回 True=已启用"""
        if self._allowed_servers is None:
            all_names = set(self.servers.keys())
            self._allowed_servers = all_names - {name}
            return False
        if name in self._allowed_servers:
            self._allowed_servers.discard(name)
            return False
        self._allowed_servers.add(name)
        return True

    def is_server_enabled(self, name: str) -> bool:
        return self._allowed_servers is None or name in self._allowed_servers

    def set_allowed_servers(self, names: list):
        self._allowed_servers = set(names) if names is not None else None

    def get_all_tools_openai_format(self) -> List[dict]:
        tools = []
        for server_name, info in self.servers.items():
            if not info.connected or (self._allowed_servers is not None and server_name not in self._allowed_servers):
                continue
            for t in info.tools:
                input_schema = {}
                if hasattr(t, 'inputSchema') and t.inputSchema:
                    input_schema = t.inputSchema
                elif hasattr(t, 'input_schema') and t.input_schema:
                    input_schema = t.input_schema

                tools.append({
                    "type": "function",
                    "function": {
                        "name": f"mcp__{server_name}__{t.name}",
                        "description": f"[MCP:{server_name}] {t.description or t.name}",
                        "parameters": input_schema,
                    },
                })
        return tools

    def get_tool_info_list(self) -> List[dict]:
        """返回所有已连接 server 的工具（含禁用的，用于 UI 显示）"""
        result = []
        for server_name, info in self.servers.items():
            if not info.connected:
                continue
            for t in info.tools:
                result.append({
                    "name": t.name,
                    "server": server_name,
                    "description": t.description or "",
                })
        return result

    def get_server_status(self) -> List[dict]:
        result = []
        seen = set()
        for name, info in self.servers.items():
            seen.add(name)
            result.append({
                "name": name,
                "connected": info.connected,
                "tools_count": len(info.tools),
                "error": info.error,
                "disabled": self._allowed_servers is not None and name not in self._allowed_servers,
                "config_disabled": False,
            })
        for name, cfg in self._all_configs.items():
            if name not in seen and not cfg.get("enabled", True):
                result.append({
                    "name": name,
                    "connected": False,
                    "tools_count": 0,
                    "error": "",
                    "disabled": False,
                    "config_disabled": True,
                })
        return result

    async def call_tool(self, full_tool_name: str, arguments: dict) -> str:
        """调用 MCP 工具。full_tool_name 格式: mcp__{server}__{tool}"""
        parts = full_tool_name.split("__", 2)
        if len(parts) != 3 or parts[0] != "mcp":
            return f"[错误] 无效的 MCP 工具名: {full_tool_name}"

        server_name = parts[1]
        tool_name = parts[2]

        if self._allowed_servers is not None and server_name not in self._allowed_servers:
            return f"[已拦截] MCP Server '{server_name}' 不在允许列表中"

        info = self.servers.get(server_name)
        if not info or not info.connected or not info.session:
            return f"[错误] MCP Server '{server_name}' 未连接"

        try:
            result = await asyncio.wait_for(
                info.session.call_tool(tool_name, arguments=arguments),
                timeout=60,
            )

            texts = []
            for item in result.content:
                if hasattr(item, 'text'):
                    texts.append(item.text)
                elif hasattr(item, 'data'):
                    texts.append(str(item.data))
                else:
                    texts.append(str(item))

            return "\n".join(texts) if texts else "(空结果)"

        except asyncio.TimeoutError:
            return f"[超时] MCP 工具 {tool_name} 执行超时(60s)"
        except Exception as e:
            return f"[错误] MCP 工具调用失败: {type(e).__name__}: {e}"

    def is_mcp_tool(self, tool_name: str) -> bool:
        return tool_name.startswith("mcp__")
