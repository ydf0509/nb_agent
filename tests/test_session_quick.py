"""快速验证 SessionStore"""
import tempfile
import os

from nb_agent.session import SessionStore

db = os.path.join(tempfile.mkdtemp(), "test.db")
store = SessionStore(db)
store.create_session("test1", title="Hello", model_id="gpt-4")
store.save_message("test1", "user", "Hi there")
store.save_message("test1", "assistant", "Hello!")
msgs = store.get_messages("test1")
sessions = store.list_sessions()
print(f"Messages: {len(msgs)}, Sessions: {len(sessions)}")
print(f"First msg: role={msgs[0]['role']}, content={msgs[0]['content']}")
print(f"Session title: {sessions[0]['title']}")
print("Session store OK")
