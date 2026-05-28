"""测试 SessionStore (SQLModel)"""
import os
import tempfile
from nb_agent.session import SessionStore


def _make_store():
    db = os.path.join(tempfile.mkdtemp(), "test.db")
    return SessionStore(db)


def test_create_and_list():
    store = _make_store()
    store.create_session("s1", title="Test 1")
    store.create_session("s2", title="Test 2")
    sessions = store.list_sessions()
    assert len(sessions) == 2


def test_save_and_get_messages():
    store = _make_store()
    store.create_session("s1", title="Test")
    store.save_message("s1", "user", "Hello")
    store.save_message("s1", "assistant", "Hi!")
    msgs = store.get_messages("s1")
    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"
    assert msgs[1]["content"] == "Hi!"


def test_update_title():
    store = _make_store()
    store.create_session("s1", title="Old")
    store.update_session_title("s1", "New Title")
    assert store.get_session_title("s1") == "New Title"


def test_delete_session():
    store = _make_store()
    store.create_session("s1")
    store.save_message("s1", "user", "msg")
    store.delete_session("s1")
    assert store.list_sessions() == []
    assert store.get_messages("s1") == []


if __name__ == "__main__":
    test_create_and_list()
    test_save_and_get_messages()
    test_update_title()
    test_delete_session()
    print("All session tests passed")
