"""nb_agent 统一日志管理 — 所有模块的 logger 集中定义

所有 logger 统一设置 is_add_stream_handler=False（不向终端输出），
仅写入各自的 log 文件。TUI 层面另有 handler 重定向兜底。
"""

from nb_log import get_logger

logger_httpx = get_logger("httpx", 
                          is_add_stream_handler=False,
                          log_filename="nb_agent_httpx.log",
                          )

logger_config = get_logger("nb_agent.config",
                            is_add_stream_handler=False,
                            log_filename="nb_agent_config.log")

logger_mcp = get_logger("nb_agent.mcp",
                         is_add_stream_handler=False,
                         log_filename="nb_agent_mcp.log")

logger_llm_call = get_logger("nb_agent.llm_call",
                         is_add_stream_handler=False,
                         log_filename="nb_agent_llm_call.log",
                         )

logger_llm_call_raw = get_logger("nb_agent.llm_call_raw",
                               is_add_stream_handler=False,
                               log_filename="nb_agent_llm_call_raw.log",
                               )