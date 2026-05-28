# demo2 — nb_agent TUI 最小示例

## 运行

```bash
cd examples/demo2
python run.py          # 直接启动
python run_verbose.py  # 启动前打印调试信息
```

## 核心代码（4 行）

```python
import tools                          # 导入即注册自定义工具
from nb_agent import load_config, AgentApp
config = load_config()
AgentApp(config).run()
```

## 完整演示

更丰富的演示（含 Skills + MCP + Agent 配置）请参考 [nb_agent_bfzs](https://github.com/xxx/nb_agent_bfzs) 项目。

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+J` / `Ctrl+Enter` | 发送消息 |
| `F1` | 帮助 |
| `F2` | 切换模型 |
| `F4` | Agent 管理（提示词+工具配置） |
| `F5` | 新建会话 |
| `F6` | 历史会话 |
| `Ctrl+P` | 命令面板 |
