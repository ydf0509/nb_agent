# Skills 系统

nb_agent 的 Skills 系统遵循 **[Agent Skills 开放规范](https://agentskills.io)**。

该规范由 Anthropic 创建并发布为开放标准，已被 26+ 平台采用（Claude、OpenAI Codex、Gemini CLI、GitHub Copilot、Cursor、VS Code 等）。

## 什么是 Skill？

Skill 是一份 Markdown 格式的操作指南，告诉 AI 在特定任务中如何一步步执行。每个 Skill 是一个包含 `SKILL.md` 文件的文件夹。

## SKILL.md 格式

文件使用 YAML Front Matter 定义元数据，后接 Markdown 正文：

```markdown
---
name: my-skill
description: 简短描述这个 Skill 的用途和触发时机
---

# Skill 标题

具体的操作步骤和指南...
```

### Front Matter 字段（agentskills.io 规范）

| 字段 | 必填 | 说明 |
|---|---|---|
| `name` | 是 | 1-64 字符，小写字母+数字+连字符，不能以连字符开头或结尾，不能有连续连字符，**必须与文件夹名一致** |
| `description` | 是 | 1-1024 字符，描述 Skill 做什么 + 什么时候用，应包含触发关键词 |
| `license` | 否 | 许可证名称或引用打包的许可证文件（如 `Apache-2.0`） |
| `compatibility` | 否 | 1-500 字符，环境要求（目标产品、系统依赖、网络访问等） |
| `metadata` | 否 | 任意键值对映射，用于自定义扩展属性（如 `author`、`version`） |
| `allowed-tools` | 否 | 空格分隔的预授权工具列表（实验性，如 `Bash(git:*) Read`） |

以下为 nb_agent 扩展字段（非 agentskills.io 规范）：

| 字段 | 必填 | 说明 |
|---|---|---|
| `paths` | 否 | 文件路径 glob 匹配模式，限定 Skill 的作用域 |
| `disable-model-invocation` | 否 | 设为 `true` 则 AI 不会自动触发，只能手动调用 |

### 完整示例

```markdown
---
name: pdf-processing
description: >-
  提取 PDF 文本、填写 PDF 表单、合并多个 PDF。
  当用户提到 PDF、表单、文档提取时使用。
license: Apache-2.0
compatibility: Requires Python 3.10+ and poppler-utils
metadata:
  author: example-org
  version: "1.0"
allowed-tools: Bash(python3:*) Read Write
---

# PDF 处理 Skill

具体的操作步骤...
```

## 渐进式披露（Progressive Disclosure）

Agent Skills 规范的核心设计模式：

1. **Discovery（发现）**：启动时只加载 `name` + `description`，注入到 system prompt 的 Skills 清单中
2. **Activation（激活）**：当任务匹配某个 Skill 时，AI 调用 `view_skill()` 工具加载完整 SKILL.md 内容
3. **Execution（执行）**：AI 按照指南步骤执行任务，按需加载 scripts/、references/ 等资源

这样既节省 Context Window（token），又不丢失功能。

## Skill 存放位置

| 来源 | 路径 | 说明 |
|---|---|---|
| 内置 | `nb_agent/skills/builtin/` | 随 nb_agent 安装 |
| 全局 | `~/.nb_agent/skills/` 或 `~/.agents/skills/` | 用户级，所有项目共享 |
| 项目 | `<project>/.nb_agent/skills/` 或 `<project>/.agents/skills/` | 项目级，跟随项目 |

## 创建 Skill

```
my-skill/                 ← 文件夹名
├── SKILL.md              # 必需：元数据 + 操作指南
├── scripts/              # 可选：可执行脚本
├── references/           # 可选：参考文档
└── assets/               # 可选：模板、资源文件
```

1. 在上述任一目录下创建子文件夹（如 `my-skill/`）
2. 在子文件夹中创建 `SKILL.md` 文件
3. **`name` 字段必须与文件夹名一致**（如文件夹叫 `my-skill`，则 `name: my-skill`）
4. 重启 nb_agent 即可发现新 Skill

## 相关链接

- [Agent Skills 官网](https://agentskills.io)
- [Agent Skills 规范](https://agentskills.io/specification)
- [GitHub 仓库](https://github.com/agentskills/agentskills)
- [示例 Skills](https://github.com/anthropics/skills)
