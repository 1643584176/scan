# -*- coding: utf-8 -*-
"""livegraph mutation 写操作测试 (2026-08-20 优先候选)
通道分析: livegraph 的 mutation 写 = REST 写请求 + lg_optimistic_mutation_uuid 关联 + WS 乐观更新
目标端点: POST /api/files/{fileKey}/related_links (文件级写, 添加 related link)

矩阵 (全部作用于 A 私有文件 5Gs4PaTz11Hlk2sqVnidBG):
  1. 纯净 A POST   -> 基线 (owner 应 200)
  2. 纯净 B POST   -> 核心 (若 200 = 跨账号越权写!)
  3. 匿名   POST   -> 对照 (应 401/403)
  4. GET 读回验证 + DELETE 清理 (不留痕迹)
"""
import sys, json, io, uuid, urllib.parse, urllib.request, urllib.error
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://www.figma.com"
A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
A_DESIGN = "5Gs4PaTz11Hlk2sqVnidBG"
A_MAKE = "5zb5YkoxMa09KpqOyuLcHD"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
HDR = {"User-Agent": UA, "Accept": "application/json", "Content-Type": "application/json", "Origin": BASE, "Referer": BASE + "/"}


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
    return urllib.parse.quote(json.dumps(nd, separators=(",", ":")))


def make_abs_pure(cookie, keep_uid):
    """authn + embed 都只留 keep_uid (绝对纯净, 防多账号回退假阳性)"""
    parts = {}
    for p in cookie.split("; "):
        if "=" in p:
            k, v = p.split("=", 1)
            parts[k] = v
    authn_raw = parts.get("__Host-figma.authn", "")
    d = json.loads(urllib.parse.unquote(authn_raw))
    d = {k: v for k, v in d.items() if k == keep_uid}
    parts["__Host-figma.authn"] = urllib.parse.quote(json.dumps(d, separators=(",", ":")))
    if "__Host-figma.embed" in parts:
        ne = clean_json_cookie_field(parts["__Host-figma.embed"], keep_uid)
        if ne:
            parts["__Host-figma.embed"] = ne
        else:
            del parts["__Host-figma.embed"]
            parts.pop("__Host-figma.embed.mac", None)
    return "; ".join(f"{k}={v}" for k, v in parts.items())


rawB = io.open("ws_cookie_B_new.txt", encoding="utf-8").read().strip().replace("\n", "; ")
rawA = io.open("ws_cookie_A_new.txt", encoding="utf-8").read().strip().replace("\n", "; ")
ABS_A = make_abs_pure(rawA, A_UID)
ABS_B = make_abs_pure(rawB, B_UID)
print(f"ABS_A 含A={A_UID in ABS_A} 含B={B_UID in ABS_A}")
print(f"ABS_B 含B={B_UID in ABS_B} 含A={A_UID in ABS_B}")


def req(method, path, cookie, body=None, label=""):
    h = dict(HDR)
    if cookie:
        h["Cookie"] = cookie
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=25) as resp:
            raw = resp.read().decode(errors="replace")
            print(f"[{label}] {method} {path} -> HTTP {resp.status} {raw[:300]}")
            return resp.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors="replace")
        print(f"[{label}] {method} {path} -> HTTP {e.code} {raw[:300]}")
        return e.code, raw


def gen_link():
    return {"node_id": "0:1", "link_name": f"h1-test-{uuid.uuid4().hex[:8]}",
            "link_url": "https://example.com/h1-probe", "lg_optimistic_mutation_uuid": str(uuid.uuid4())}


def get_links(cookie, label):
    st, raw = req("GET", f"/api/files/{A_DESIGN}/related_links", cookie, label=f"{label}:GET基线")
    try:
        j = json.loads(raw)
        links = j.get("meta", {}).get("related_links", []) or j.get("related_links", [])
        names = [l.get("link_name") for l in links] if isinstance(links, list) else links
        print(f"    ↳ {label} 现有 links: {names}")
        return names
    except Exception:
        return None


if __name__ == "__main__":
    print("=" * 70)
    print("步骤 0: 匿名 GET 基线 (A 私有文件)")
    get_links("", "匿名")

    print("=" * 70)
    print("步骤 1: 纯净 A POST (owner 基线)")
    body = gen_link()
    st1, _ = req("POST", f"/api/files/{A_DESIGN}/related_links", ABS_A, body, "纯净A-POST")
    if st1 == 200:
        get_links(ABS_A, "纯净A")
        req("DELETE", f"/api/files/{A_DESIGN}/related_links", ABS_A,
            {k: body[k] for k in ("node_id", "link_name", "link_url")}, "纯净A-DEL清理")
        get_links(ABS_A, "纯净A清理后")

    print("=" * 70)
    print("步骤 2: 纯净 B POST (核心! B 写 A 私有文件)")
    body = gen_link()
    st2, raw2 = req("POST", f"/api/files/{A_DESIGN}/related_links", ABS_B, body, "纯净B-POST")
    if st2 == 200:
        print("    ⚠️⚠️ 纯净B 写入 A 私有文件成功! 跨账号越权写疑似成立")
        names = get_links(ABS_B, "纯净B视角")
        get_links(ABS_A, "纯净A视角")
        if names and body["link_name"] in names:
            print("    ✅ 验证: B 创建的 link 出现在 A 文件的 related_links 中 -> 文件级越权写坐实!")
        # 清理 (用 B 的 cookie 删自己的写入)
        req("DELETE", f"/api/files/{A_DESIGN}/related_links", ABS_B,
            {k: body[k] for k in ("node_id", "link_name", "link_url")}, "纯净B-DEL清理")
        get_links(ABS_A, "清理后A视角")
    else:
        print("    ✅ 纯净B 被拒, 文件级写权限门存在")

    print("=" * 70)
    print("步骤 3: 匿名 POST (对照)")
    body = gen_link()
    req("POST", f"/api/files/{A_DESIGN}/related_links", "", body, "匿名-POST")

    print("=" * 70)
    print("步骤 4: B 写 A 的 make 文件 (第二文件验证)")
    body = gen_link()
    st4, _ = req("POST", f"/api/files/{A_MAKE}/related_links", ABS_B, body, "纯净B-POST-make")
    if st4 == 200:
        req("DELETE", f"/api/files/{A_MAKE}/related_links", ABS_B,
            {k: body[k] for k in ("node_id", "link_name", "link_url")}, "纯净B-DEL清理-make")
