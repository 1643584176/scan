# -*- coding: utf-8 -*-
# peek last N REAL user queries (strip injected system context)
import json, re

path = r"C:/Users/tndc2/.qoder/cache/projects/scan-72ece876/conversation-history/c354f2ed/c354f2ed.jsonl"
n = 100
msgs = []
with open(path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if obj.get("role") != "user":
            continue
        m = obj.get("message", {})
        c = m.get("content")
        txt = ""
        if isinstance(c, str):
            txt = c
        elif isinstance(c, list):
            parts = []
            for p in c:
                if isinstance(p, dict):
                    parts.append(p.get("text", "") or p.get("content", ""))
                else:
                    parts.append(str(p))
            txt = " ".join(parts)
        mq = re.search(r"<user_query>(.*?)</user_query>", txt, re.S)
        q = mq.group(1).strip() if mq else txt.strip()
        # skip pure system-injected blocks
        if q.startswith("<ide_context>") or q.startswith("<system-reminder>") or q.startswith("<project_instructions>"):
            continue
        msgs.append((obj.get("timestamp", ""), q[:1500]))

for ts, t in msgs[-n:]:
    print("=" * 60)
    print(ts)
    print(t)
