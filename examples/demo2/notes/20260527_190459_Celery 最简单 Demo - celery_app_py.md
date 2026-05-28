---
title: Celery 最简单 Demo - celery_app.py
created: 2026-05-27T19:04:59.408895
tags: celery, demo, python
---

from celery import Celery

# 创建 Celery 应用
# broker: 消息代理（这里用 Redis）
# backend: 结果存储（这里用 Redis）
app = Celery(
    'demo',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)
