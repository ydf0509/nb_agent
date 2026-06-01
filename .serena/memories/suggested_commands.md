# nb_agent 常用命令 (Windows 环境)

## 运行

```bash
# 启动 TUI（项目根目录）
nb_agent

# 指定配置文件
nb_agent --config ./config.jsonc

# 非交互模式（一次对话）
nb_agent run "你好，请帮我分析这段代码"

# 从文件读取 prompt
nb_agent run -f prompt.txt

# 查看历史会话
nb_agent sessions list
```

## 开发运行

```bash
# 直接运行 main 模块（调试用）
python -m nb_agent.main

# 单独运行 TUI
python -c "from nb_agent.main import main; main()"
```

## 安装/构建

```bash
# pip 安装当前项目
pip install -e .

# 安装开发依赖
pip install -e ".[dev]"
```

## 测试

```bash
# 运行测试（pytest）
pytest

# 带详细输出
pytest -v
```

## Git 相关

```bash
# 查看状态
git status

# 查看 diff
git diff

# 添加并提交
git add -A && git commit -m "message"
```

## 系统工具 (Windows 注意)

```bash
# 查看目录结构（Windows 用 dir，不能用 ls）
dir /s /b

# Python 路径
where python

# 查找文件
dir /s /b *.py | findstr "keyword"
```
