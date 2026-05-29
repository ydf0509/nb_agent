# config.jsonc 配置说明

## 概述

`config.jsonc` 是 nb_agent 的 JSONC 格式配置文件（JSONC 支持 `//` 注释和尾逗号），放在项目根目录即可。

**配置优先级：** CLI 参数 > 环境变量 > 项目级 `./config.jsonc` > 全局 `~/.nb_agent/config.jsonc` > 默认值

**环境变量替换：** 配置中的任何字符串值都可以使用 `{env:变量名}` 语法从环境变量读取，缺失的环境变量会被替换为空字符串。

```jsonc
// 示例：api_key 从环境变量 DEEPSEEK_API_KEY 读取
"api_key": "{env:DEEPSEEK_API_KEY}"
```

---

## 完整配置结构

```jsonc
{
    "provider": { /* LLM 提供商 */ },
    "agent":    { /* Agent 行为 */ },
    "mcp":      { /* MCP Server */ },
    "approval": { /* 审批规则 */ },
    "session":  { /* 会话存储 */ },
    "ui":       { /* 界面设置 */ }
}
```

---

## 1. provider — LLM 提供商

配置一个或多个 LLM 提供商（API 代理），每个提供商下可定义多个模型。

```jsonc
"provider": {
    "提供商ID，随意命名": {
        "name":     "显示名称（可选，UI 中展示）",
        "base_url": "API 地址，例如 https://api.deepseek.com/v1",
        "api_key":  "API Key，支持 {env:XXX}",
        "models": {
            "模型ID": {
                "name":  "显示名称",
                "limit": {
                    "context": 64000,   // 上下文窗口 token 数
                    "output":  8192     // 最大输出 token 数
                }
            }
        }
    }
}
```

### 完整示例

**示例 A：直连 DeepSeek 官方 API**

```jsonc
"provider": {
    "deepseek": {
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "api_key": "{env:DEEPSEEK_API_KEY}",
        "models": {
            "deepseek-chat": {
                "name": "DeepSeek V3",
                "limit": { "context": 64000, "output": 8192 }
            },
            "deepseek-reasoner": {
                "name": "DeepSeek R1",
                "limit": { "context": 64000, "output": 8192 }
            }
        }
    }
}
```

**示例 B：通过 LiteLLM Proxy 聚合多个模型**

```jsonc
"provider": {
    "litellm": {
        "name": "LiteLLM Proxy",
        "base_url": "http://localhost:4000/v1",
        "api_key": "not-needed",
        "models": {
            "aku-qwen3.5-397b": {
                "name": "Qwen3.5 397B",
                "limit": { "context": 131072, "output": 65536 }
            },
            "ark-deepseek-v3.2": {
                "name": "DeepSeek V3.2",
                "limit": { "context": 131072, "output": 65536 }
            }
        }
    }
}
```

> **模型 ID 规则：** `provider` 下的模型 ID 必须与 API 返回的 `model` 字段一致。LiteLLM 的模型 ID 就是 `litellm` 路由中配置的名称。

---

## 2. agent — Agent 行为

```jsonc
"agent": {
    "system_prompt":       "系统提示词，定义 AI 的角色和行为",
    "default_model":       "默认使用的模型 ID（对应 provider 中某个模型）",
    "max_context_tokens":  0,       // 上下文窗口上限，0=使用模型默认值
    "streaming":           true     // 是否启用流式输出
}
```

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `system_prompt` | string | `"你是一个智能助手。"` | 系统提示词，会追加当前日期和 Skills 清单 |
| `default_model` | string | 空=自动选第一个 | 默认使用的模型 ID |
| `max_context_tokens` | int | `0` | 上下文窗口上限，0 表示使用模型的 context limit |
| `streaming` | bool | `true` | 流式输出开关，false 为非流式 |

---

## 3. mcp — MCP Server 配置

nb_agent 支持四种 MCP 传输方式：

| 类型 | 说明 | 适用场景 |
|------|------|----------|
| `local` | 启动子进程，通过 stdio 通信 | 本地安装的工具/自定义 MCP |
| `sse` | 通过 SSE 连接远程 MCP Server | Docker 部署的 Web 服务 |
| `http` / `streamableHttp` | 通过 Streamable HTTP 连接 | 独立启动的 HTTP MCP 服务 |

### 3.1 local — 本地 stdio 方式

```jsonc
"mcp_server_name": {
    "type":    "local",
    "command": "可执行文件",                          // 字符串
    // 或
    "command": ["python", "mcp_servers/xxx.py"],     // 数组（推荐，自动拆分）
    // 可选字段：
    "args":          ["--port", "3000"],             // 额外参数，会追加到 command 后面
    "environment":   { "REDIS_URL": "redis://..." }, // 自定义环境变量
    "cwd":           "D:/your/project",              // 工作目录，默认=项目根目录
    "init_timeout":  60,                             // 初始化超时秒数，默认 60
    "enabled":       true                            // 是否启用，默认 true
}
```

**`command` 是字符串还是数组？**

两种写法都支持：
- **字符串**：`"command": "python mcp_servers/xxx.py"` — 简单场景用
- **数组（推荐）**：`"command": ["python", "mcp_servers/xxx.py"]` — 带空格路径更安全

`args` 是可选的，它会被追加到 `command` 后面。下面两种写法等价：

```jsonc
// 写法一：全写在 command 里
"command": ["serena", "start-mcp-server", "--project", "D:/codes/my_project"]

// 写法二：拆分 command + args
"command": "serena",
"args":    ["start-mcp-server", "--project", "D:/codes/my_project"]
```

**local 模式示例：**

```jsonc
"mcp": {
    // 示例 1：启动自定义 FastMCP（你写的 Python MCP Server）
    "bookmark": {
        "type": "local",
        "command": ["python", "mcp_servers/bookmark_server.py"],
        "enabled": true
    },

    // 示例 2：带环境变量的 Redis 工具 MCP
    "redis-tools": {
        "type": "local",
        "command": ["python", "mcp_servers/redis_tools_server.py"],
        "environment": {
            "REDIS_URL": "redis://localhost:6379"
        },
        "enabled": true
    },

    // 示例 3：npx 启动第三方 MCP
    "context7": {
        "type": "local",
        "command": ["npx", "-y", "@upstash/context7-mcp@latest"],
        "enabled": false
    },

    // 示例 4：文件系统 MCP（必须指定目录绝对路径）
    "filesystem": {
        "type": "local",
        "command": ["npx", "-y", "@modelcontextprotocol/server-filesystem", "D:/codes/my_project"],
        "enabled": false
    },

    // 示例 5：Serena 编程 MCP
    "serena": {
        "type": "local",
        "command": ["serena", "start-mcp-server", "--project", "D:/codes/my_project"],
        "enabled": false
    }
}
```

### 3.2 sse — SSE 连接方式

```jsonc
"mcp_server_name": {
    "type":    "sse",
    "url":     "http://localhost:3000/sse",     // SSE 端点地址
    "headers": { "Authorization": "..." },       // 可选：自定义请求头
    "init_timeout": 30,                          // 可选：初始化超时秒数，默认 30
    "enabled": true                              // 可选：默认 true
}
```

**示例：**

```jsonc
// 先启动：docker run -d --name web-search -p 3000:3000 -e ENABLE_CORS=true ghcr.io/aas-ee/open-web-search:latest
"web-search": {
    "type": "sse",
    "url": "http://localhost:3000/sse",
    "enabled": true
}
```

### 3.3 http / streamableHttp — HTTP 连接方式

`http` 是 `streamableHttp` 的别名，两者完全等价。

```jsonc
"mcp_server_name": {
    "type":    "http",                           // 或 "streamableHttp"
    "url":     "http://localhost:9101/mcp",      // MCP 端点地址
    "headers": { "Authorization": "..." },        // 可选：自定义请求头
    "init_timeout": 30,                           // 可选：初始化超时秒数，默认 30
    "enabled": true                               // 可选：默认 true
}
```

**示例：**

```jsonc
// 先启动 nbrag 服务：uvx nbrag --transport streamable-http --port 9101
// 环境变量：NBRAG_API_KEY（访问 LLM 所需）
"nbrag": {
    "type": "http",
    "url": "http://localhost:9101/mcp"
}
```

---

## 4. approval — 审批规则

危险工具执行前，TUI 会弹窗让用户确认。

```jsonc
"approval": {
    "dangerous_tools": [
        "note__delete_note",                     // 工具名（精确匹配）
        "mcp__redis-tools__redis_smart_set"      // MCP 工具名格式: mcp__{server}__{tool}
    ],
    "auto_approve": false                        // true=所有操作自动放行（不弹窗）
}
```

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `dangerous_tools` | string[] | `[]` | 需要审批的工具名列表 |
| `auto_approve` | bool | `false` | true = 全部自动放行，不弹窗 |

**工具名规则：**
- 内置工具：直接写函数名，如 `note__delete_note`
- MCP 工具：格式为 `mcp__服务器名__工具名`，如 `mcp__redis-tools__redis_smart_set`

> 如需更灵活的审批逻辑（如按参数值判断），可编写 `approval_rules.py` 自定义规则函数，代码的表达能力比配置更强。

---

## 5. session — 会话存储

```jsonc
"session": {
    "db_path": ""    // 空字符串 = 默认 ~/.nb_agent/sessions.db
}
```

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `db_path` | string | `""` | SQLite 数据库路径，空 = `~/.nb_agent/sessions.db` |

会话数据包括：对话历史、Agent 预设配置（工具组/MCP/Skills 开关）。

---

## 6. ui — 界面设置

```jsonc
"ui": {
    "theme":             "dark",    // 主题：目前仅 "dark"
    "show_tool_panel":   true,      // 是否显示右侧工具/MCP/模型面板
    "show_token_usage":  true       // 是否在底部状态栏显示 Token 用量
}
```

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `theme` | string | `"dark"` | 主题，目前仅支持 `"dark"` |
| `show_tool_panel` | bool | `true` | 右侧面板开关（工具/MCP/模型列表） |
| `show_token_usage` | bool | `true` | 底部状态栏 Token 统计 |

---

## 完整配置示例

```jsonc
{
    "agent": {
        "system_prompt": "你是一个智能助手，可以调用工具来帮助用户解决问题。请用中文回答。",
        "default_model": "deepseek-chat",
        "streaming": true
    },

    "provider": {
        "deepseek": {
            "name": "DeepSeek",
            "base_url": "https://api.deepseek.com/v1",
            "api_key": "{env:DEEPSEEK_API_KEY}",
            "models": {
                "deepseek-chat": {
                    "name": "DeepSeek V3",
                    "limit": { "context": 64000, "output": 8192 }
                },
                "deepseek-reasoner": {
                    "name": "DeepSeek R1",
                    "limit": { "context": 64000, "output": 8192 }
                }
            }
        }
    },

    "mcp": {
        "context7": {
            "type": "local",
            "command": ["npx", "-y", "@upstash/context7-mcp@latest"],
            "enabled": false
        },
        "serena": {
            "type": "local",
            "command": ["serena", "start-mcp-server", "--project", "D:/codes/my_project"],
            "enabled": false
        },
        "nbrag": {
            "type": "http",
            "url": "http://localhost:9101/mcp"
        }
    },

    "approval": {
        "dangerous_tools": [],
        "auto_approve": false
    },

    "session": {
        "db_path": ""
    },

    "ui": {
        "theme": "dark",
        "show_tool_panel": true,
        "show_token_usage": true
    }
}
```

---

## 常见问题

**Q: 如何设置 API Key？**

方式一（推荐）：使用环境变量替换 `"api_key": "{env:DEEPSEEK_API_KEY}"`，然后在终端设置 `$env:DEEPSEEK_API_KEY="sk-xxx"` 或写入 `.env` 文件。

方式二：直接写在配置里（不推荐，仅限本地开发）。

**Q: MCP 的 `command` 用字符串还是数组？**

都支持。带空格、特殊字符的路径用数组更安全。`args` 可选，会被追加到 `command` 后面。

**Q: `http` 和 `streamableHttp` 有什么区别？**

没有区别，`http` 是 `streamableHttp` 的别名。

**Q: MCP 怎么传环境变量？**

使用 `environment` 字段，例如：

```jsonc
"my-mcp": {
    "type": "local",
    "command": ["python", "server.py"],
    "environment": {
        "NBRAG_API_KEY": "{env:NBRAG_API_KEY}",
        "MY_VAR": "my_value"
    }
}
```

**Q: 配置写错了怎么排查？**

启动时控制台会打印 MCP 连接状态和错误信息。也可以在 TUI 右侧面板查看每个 MCP Server 的连接状态和错误原因。
