"""重建数据库（删旧列，用新 model schema）"""
import sqlite3, json, os

db = os.path.expanduser("~/.nb_agent/sessions.db")
conn = sqlite3.connect(db)
cur = conn.cursor()

# 备份用户 agent
cur.execute("SELECT id, name, system_prompt, is_builtin, created_at, updated_at FROM agent_configs WHERE is_builtin = 0")
agents = cur.fetchall()
print(f"备份 {len(agents)} 个用户 Agent")

# 重建表
cur.execute("DROP TABLE IF EXISTS agent_configs")
cur.execute("""CREATE TABLE agent_configs (
    id VARCHAR PRIMARY KEY,
    name VARCHAR DEFAULT '',
    system_prompt VARCHAR DEFAULT '',
    allowed_tool_groups_json VARCHAR DEFAULT 'null',
    allowed_mcp_servers_json VARCHAR DEFAULT 'null',
    allowed_skills_json VARCHAR DEFAULT 'null',
    is_builtin BOOLEAN DEFAULT 0,
    created_at VARCHAR DEFAULT '',
    updated_at VARCHAR DEFAULT ''
)""")

# 恢复（allowed 全部设为 null = 全部允许）
for a in agents:
    cur.execute(
        "INSERT INTO agent_configs VALUES (?,?,?,'null','null','null',?,?,?)",
        (a[0], a[1], a[2], a[3], a[4], a[5])
    )
    print(f"  恢复: {a[1]}")

conn.commit()

# 验证
cur.execute("PRAGMA table_info(agent_configs)")
cols = [c[1] for c in cur.fetchall()]
print(f"\n新表列: {cols}")
conn.close()
print("Done!")
