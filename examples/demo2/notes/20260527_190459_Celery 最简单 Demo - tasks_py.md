---
title: Celery 最简单 Demo - tasks.py
created: 2026-05-27T19:04:59.411408
tags: celery, demo, python
---

from celery_app import app
import time

@app.task
def add(x, y):
    """最简单的加法任务"""
    print(f"📝 正在计算: {x} + {y}")
    time.sleep(2)  # 模拟耗时操作
    result = x + y
    print(f"✅ 计算结果: {result}")
    return result

@app.task
def hello(name):
    """打招呼任务"""
    return f"Hello, {name}!"
