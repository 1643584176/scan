# -*- coding: utf-8 -*-
"""考古:实时通道(websocket/actioncable/pusher/stream)(2026-09-08)"""
import re

with open(r"D:\scan\h1kit\_h1x4_app.js", "r", encoding="utf-8", errors="replace") as f:
    data = f.read()

kws = ["actioncable", "ActionCable", "websocket", "WebSocket", "pusher", "Pusher", "socket.io",
       "EventSource", "text/event-stream", "subscribe", "cable", "ably", "Ably", "centrifuge",
       "graphql-ws", "subscriptions-transport"]
for kw in kws:
    hits = [m.start() for m in re.finditer(re.escape(kw), data)]
    if hits:
        print(f"== {kw}: {len(hits)}")
        # 打印前 2 个上下文(短)
        for h in hits[:2]:
            print("   >", data[max(0, h - 120):h + 180].replace("\n", " ")[:300])
