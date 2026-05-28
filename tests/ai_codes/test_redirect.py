"""测试 nb_log 日志是否能被完全重定向"""
import sys, io, logging, os

# 保存最底层的终端 fd（不会被 monkey patch 影响）
_terminal_fd = os.dup(1)

def _write_terminal(msg):
    os.write(_terminal_fd, (msg + "\n").encode())

from nb_log import get_logger
import nb_log.monkey_sys_std as _std_mod
import nb_log

lg = get_logger('test_full_fix', is_add_stream_handler=True)

buf = io.StringIO()
original_stdout = sys.stdout
original_stderr = sys.stderr
sys.stdout = buf
sys.stderr = buf

for lo in [logging.getLogger()] + list(logging.Logger.manager.loggerDict.values()):
    if not isinstance(lo, logging.Logger):
        continue
    for h in lo.handlers:
        if hasattr(h, 'stream') and h.stream in (original_stdout, original_stderr):
            h.stream = buf

_std_mod.stdout_raw = buf.write
_std_mod.stderr_raw = buf.write
nb_log.stdout_raw = buf.write
nb_log.stderr_raw = buf.write

lg.info('SHOULD_BE_CAPTURED')
lg.warning('WARNING_TOO')

captured = buf.getvalue()
_write_terminal(f"captured length: {len(captured)}")
_write_terminal(f"has CAPTURED: {'SHOULD_BE_CAPTURED' in captured}")
_write_terminal(f"has WARNING: {'WARNING_TOO' in captured}")
_write_terminal("PASS - terminal is clean above this line")
