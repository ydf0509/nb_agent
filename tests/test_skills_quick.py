"""快速验证 Skills 系统"""
from nb_agent.skills import SkillManager

mgr = SkillManager()
mgr.discover()
manifest = mgr.get_manifest()
print(f"Skills discovered: {len(manifest)}")
for s in manifest:
    print(f"  - {s['name']}: {s['description'][:60]}")

result = mgr.view_skill("code-review")
print(f"view_skill OK: {result['success']}")
print(f"Content preview: {result['content'][:80]}...")

schema = mgr.get_view_skill_schema()
print(f"Schema function name: {schema['function']['name']}")
print("Skills system OK")
