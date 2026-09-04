# -*- coding: utf-8 -*-
"""Supabase dashboard 可达性只读诊断 (≤5 requests, 全部只读无认证)"""
import ssl
import socket
import urllib.request
import urllib.error

TARGETS = [
    ("dashboard", "https://supabase.com/dashboard"),
    ("status",    "https://status.supabase.com/"),
    ("api",       "https://api.supabase.com/"),
]

ctx = ssl.create_default_context()
ctx.check_hostname = True


def probe(name, url, method="HEAD"):
    try:
        req = urllib.request.Request(url, method=method, headers={"User-Agent": "Mozilla/5.0"})
        t0 = __import__("time").time()
        with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
            dt = __import__("time").time() - t0
            body = r.read(200).decode("utf-8", "ignore") if method == "GET" else ""
            print(f"[OK]   {name:10s} HTTP {r.status}  {dt*1000:.0f}ms  final={r.geturl()[:60]}  body_head={body[:80]!r}")
    except urllib.error.HTTPError as e:
        print(f"[HTTP] {name:10s} HTTP {e.code}  (访问可达, 服务端返回错误码)")
    except urllib.error.URLError as e:
        print(f"[FAIL] {name:10s} 网络层失败: {e.reason}")
    except socket.timeout:
        print(f"[FAIL] {name:10s} 超时 >10s")
    except Exception as e:
        print(f"[FAIL] {name:10s} 异常: {type(e).__name__}: {e}")


if __name__ == "__main__":
    # 1) TCP 连通性
    for host, port in [("supabase.com", 443), ("api.supabase.com", 443)]:
        try:
            s = socket.create_connection((host, port), timeout=8)
            print(f"[TCP ] {host}:{port} 连接成功")
            s.close()
        except Exception as e:
            print(f"[TCP ] {host}:{port} 连接失败: {e}")
    # 2) HTTP 探测
    probe(*TARGETS[0])
    probe(*TARGETS[1])
    probe(*TARGETS[2])
