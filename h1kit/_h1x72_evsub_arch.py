# -*- coding: utf-8 -*-
"""考古:event_subscriber 引用上下文 + 事件流机制(2026-09-08)"""
import re

with open(r"D:\scan\h1kit\_h1x4_app.js", "r", encoding="utf-8", errors="replace") as f:
    data = f.read()

for kw in ["event_subscriber", "EventSubscriber", "eventSubscriber"]:
    for m in re.finditer(re.escape(kw), data):
        ctx = data[max(0, m.start() - 250):m.start() + 250].replace("\n", " ")
        print(f"[{kw}] >>>", ctx[:450])
        print("---")

# 找所有 chunk 文件名(可能含 event 字样)
print("== chunk 列表(含 event/cable/stream):")
for m in re.finditer(r"static/([a-z_0-9]+-[A-Za-z0-9_-]+\.js)", data):
    n = m.group(1)
    if re.search(r"event|sub|cable|stream|notif|realtime|channel", n, re.I):
        print("   ", n)
