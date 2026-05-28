"""测试 Skills 系统"""
from nb_agent.skills import SkillManager


def test_discover_builtin():
    mgr = SkillManager()
    mgr.discover()
    manifest = mgr.get_manifest()
    names = [s["name"] for s in manifest]
    assert "code-review" in names
    assert "explain-code" in names
    assert "refactor" in names


def test_description_includes_when():
    mgr = SkillManager()
    mgr.discover()
    manifest = mgr.get_manifest()
    for s in manifest:
        assert len(s["description"]) > 20, f"Skill {s['name']} description too short"


def test_get_all_skills():
    mgr = SkillManager()
    mgr.discover()
    all_skills = mgr.get_all_skills()
    assert len(all_skills) >= 3
    for s in all_skills:
        assert "manual_only" in s


def test_view_skill():
    mgr = SkillManager()
    mgr.discover()
    result = mgr.view_skill("code-review")
    assert result["success"] is True
    assert len(result["content"]) > 50


def test_view_nonexistent_skill():
    mgr = SkillManager()
    mgr.discover()
    result = mgr.view_skill("nonexistent")
    assert result["success"] is False


def test_view_skill_schema():
    mgr = SkillManager()
    schema = mgr.get_view_skill_schema()
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "view_skill"


if __name__ == "__main__":
    test_discover_builtin()
    test_description_includes_when()
    test_get_all_skills()
    test_view_skill()
    test_view_nonexistent_skill()
    test_view_skill_schema()
    print("All skills tests passed")
