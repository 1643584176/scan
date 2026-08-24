# -*- coding: utf-8 -*-
"""AI Chat Threads owner 声明可信性探测
- 基线: A 用自己文件 key 列线程(确认存在)
- 注入: B 用 A 的文件 key + 自身 cookie → 若返回 A 的线程 = owner 声明未绑定身份
- 对照: B 用随机文件 key
"""
import io, json, sys, urllib.error, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
A_MAKE = "5zb5YkoxMa09KpqOyuLcHD"
B_MAKE = "76rf9byPrduayQieCWJkqV"
A_DESIGN = "5Gs4PaTz11Hlk2sqVnidBG"
RANDOM = "aaaaaaaaaaaaaaaaaaaaaa"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36"


def load(path):
    return io.open(path, encoding='utf-8').read().strip().replace('\n', '; ')


AC = load('ws_cookie_A_new.txt')
BC = load('ws_cookie_B_new.txt')


def call(label, owner_id, owner_type, uid, ck):
    headers = {"User-Agent": UA, "Accept": "application/json", "Origin": BASE,
               "Referer": BASE + "/make/" + owner_id, "Cookie": ck, "X-Figma-User-ID": uid}
    req = urllib.request.Request(
        BASE + f"/api/ai_chat/threads?owner_id={owner_id}&owner_type={owner_type}",
        headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read().decode(errors='replace')
            try:
                threads = json.loads(raw).get("meta", {}).get("threads", [])
                brief = [{"id": t.get("id"), "title": t.get("title"),
                          "privacy": t.get("privacy_mode"), "type": t.get("thread_type")} for t in threads[:8]]
                print(f"[{label}] HTTP {r.status} threads={len(threads)} {json.dumps(brief, ensure_ascii=False)[:500]}")
            except Exception:
                print(f"[{label}] HTTP {r.status} {raw[:400]}")
            return r.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors='replace')
        print(f"[{label}] HTTP {e.code} {raw[:400]}")
        return e.code, raw


print("======== /api/ai_chat/threads owner 声明探测 ========")
call("A→自己Make(基线)", A_MAKE, "file", A_UID, AC)
call("B→A的Make(注入⭐)", A_MAKE, "file", B_UID, BC)
call("B→A的Design(注入⭐)", A_DESIGN, "file", B_UID, BC)
call("B→随机key(对照)", RANDOM, "file", B_UID, BC)
call("B→A uid as owner", A_UID, "user", B_UID, BC)
