# nb_agent 任务完成检查

完成编码任务后，按以下顺序执行:

## 1. 语法检查

```bash
# Python 语法检查
python -m py_compile nb_agent/**/*.py

# 或逐个模块
python -c "import nb_agent"
```

## 2. 运行测试

```bash
pytest -v
```

## 3. 类型检查（可选）

当前项目未配置 mypy / pyright，暂不强制。

## 4. 格式检查

当前项目未配置 formatter/linter，暂不强制。
建议遵循 `mem:conventions` 中的命名和代码风格。

## 5. 实际运行验证

```bash
# 检查 CLI 是否能正常启动
nb_agent --help

# 检查配置文件格式
python -c "from nb_agent.config import load_config; cfg = load_config(); print('ok', len(cfg))"

# 非交互模式快速测试（需要 API Key 配置）
nb_agent run "简单测试，回复OK即可"
```

## 6. 记忆维护

如果修改了项目结构、依赖、约定等，更新相关 `mem:*` 记忆。
运行 `serena memories check` 确认无死链。
