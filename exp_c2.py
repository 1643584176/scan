# 沙箱内执行: 请求矩阵
# 观察: 响应来源(httpbin echo vs example.com 页面) + 注入头 + 转发头
import urllib.request, urllib.error, json

def req(path, label=""):
    r = urllib.request.Request(f"https://httpbin.org{path}")
    r.add_header("User-Agent", "exp-c2")
    try:
        with urllib.request.urlopen(r, timeout=20) as resp:
            body = resp.read().decode(errors='replace')
            try:
                d = json.loads(body)
                hdrs = d.get("headers", {})
                return (f"  {label:<14} {path:<24} -> {resp.status} "
                        f"x1={hdrs.get('X-Test-Inject','-')} "
                        f"fwd={hdrs.get('Vercel-Forwarded-Path','-')} "
                        f"oidc={'Y' if 'Vercel-Sandbox-Oidc-Token' in hdrs else 'N'} "
                        f"url={d.get('url','?')}")
            except Exception:
                # 非 JSON 响应(比如 example.com 页面)
                return f"  {label:<14} {path:<24} -> {resp.status} RAW-HTML len={len(body)}"
    except urllib.error.HTTPError as e:
        return f"  {label:<14} {path:<24} -> HTTP-{e.code}"
    except Exception as e:
        return f"  {label:<14} {path:<24} -> ERR {type(e).__name__}:{e}"

print("== 请求矩阵 ==")
for p in ["/anything", "/headers", "/api/anything", "/"]:
    print(req(p))
