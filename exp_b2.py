# 实验B2: matcher 测绘 + CA 指纹 + 头覆盖优先级
# 1) cert_fp: 拿到注入域名的证书 issuer+指纹(对比两个沙箱可判断 CA 是否共享)
# 2) matcher 矩阵: path exact=/api 下各种路径的注入触发情况
# 3) 头覆盖: 沙箱代码设置同名头, 验证防火墙是否强制覆盖
import subprocess, urllib.request, urllib.error, json

def cert_fp(host):
    r = subprocess.run(["bash", "-c",
        f"echo | timeout 10 openssl s_client -connect {host}:443 -servername {host} 2>/dev/null | openssl x509 -noout -issuer -subject -fingerprint -sha256"],
        capture_output=True, timeout=15)
    return r.stdout.decode(errors='replace').strip()

def req(path, custom_headers=None, method="GET"):
    h = dict(custom_headers or {})
    h["User-Agent"] = "exp-b2"
    r = urllib.request.Request(f"https://httpbin.org{path}", headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=12) as resp:
            d = json.loads(resp.read().decode(errors='replace'))
            hdrs = d.get("headers", {})
            inj = "X-Test-Inject" in hdrs
            return (f"  {method} {path} -> status={resp.status} "
                    f"injected={inj} val={hdrs.get('X-Test-Inject','-')} "
                    f"method={d.get('method','?')}")
    except urllib.error.HTTPError as e:
        return f"  {method} {path} -> HTTP-{e.code}"
    except Exception as e:
        return f"  {method} {path} -> ERR {type(e).__name__}:{e}"

print("== [1] 证书: httpbin.org (有注入规则, TLS被终止) ==")
try:
    print(cert_fp("httpbin.org"))
except Exception as e:
    print("  ERR", type(e).__name__, e)

print("== [2] matcher 矩阵 (path exact=/api) ==")
for p in ["/api", "/api/", "/API", "/api?q=1", "/api/v1", "/", "/anything", "/anything?path=/api"]:
    print(req(p))

print("== [3] 方法矩阵 (matcher path exact=/api) ==")
for m in ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"]:
    print(req("/api", method=m))

print("== [4] 头覆盖优先级 (沙箱代码设置同名头) ==")
print(req("/api", custom_headers={"X-Test-Inject": "MY-FORGED-VALUE", "X-Other": "keep-me"}))

print("== [5] queryString 变体 ==")
for p in ["/api?a=b", "/api?a=/api", "/api%3Fq=1", "/api%2f", "/api//", "/api/..", "/%61pi"]:
    print(req(p))
