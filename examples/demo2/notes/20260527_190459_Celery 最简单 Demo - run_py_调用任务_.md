---
title: Celery 最简单 Demo - run.py（调用任务）
created: 2026-05-27T19:04:59.413418
tags: celery, demo, python
---

from tasks import add, hello

# ──────────────────────────────
# 1️⃣ 异步发送任务（不等待结果）
# ──────────────────────────────
print("🚀 发送加法任务...")
result = add.delay(3, 5)
print(f"   任务 ID: {result.id}")
print(f"   任务状态: {result.status}")

# ──────────────────────────────
# 2️⃣ 等待并获取结果
# ──────────────────────────────
print("\n⏳ 等待结果...")
answer = result.get(timeout=10)  # 最多等10秒
print(f"🎉 3 + 5 = {answer}")

# ──────────────────────────────
# 3️⃣ 另一个任务
# ──────────────────────────────
print("\n👋 发送打招呼任务...")
hello_result = hello.delay("Celery")
print(f"   {hello_result.get(timeout=5)}")

print("\n✅ 全部完成！")
