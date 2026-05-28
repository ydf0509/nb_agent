"""一次性脚本：将旧的 allowed_skills_json='[]' 转为 'null'（仅影响默认值场景）"""
import sqlite3, os

db = os.path.expanduser("~/.nb_agent/sessions.db")
conn = sqlite3.connect(db)
cur = conn.cursor()
cur.execute("UPDATE agent_configs SET allowed_skills_json='null' WHERE allowed_skills_json='[]'")
print(f"updated {cur.rowcount} rows")
conn.commit()

cur.execute("SELECT id, name, allowed_skills_json FROM agent_configs")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]} -> skills={r[2]}")
conn.close()
