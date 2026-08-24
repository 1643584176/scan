# 实验B7: 多规则顺序/shadow + domain=* + allow-all 注入生效性验证
# 输出: 每个请求的注入头值 + 证书 issuer
import urllib.request, urllib.error, json, subprocess

def req(path, label=""):
    r = urllib.request.Request(f"https://httpbin.org{path}")
    r.add_header("User-Agent", "exp-b7")
    try:
        with urllib.request.urlopen(r, timeout=12) as resp:
            body = resp.read().decode(errors='replace')
            d = json.loads(body)
            hdrs = d.get("headers", {})
            inj = hdrs.get("X-Test-Inject", "-")
            inj2 = hdrs.get("X-Test-Inject-2", "-")
            return f"  {label:<18} {path:<20} -> {resp.status} x1={inj} x2={inj2}"
    except urllib.error.HTTPError as e:
        return f"  {label:<18} {path:<20} -> HTTP-{e.code}"
    except Exception as e:
        return f"  {label:<18} {path:<20} -> ERR {type(e).__name__}:{e}"

def cert():
    r = subprocess.run(["bash", "-c",
        "echo | timeout 10 openssl s_client -connect httpbin.org:443 -servername httpbin.org 2>/dev/null | openssl x509 -noout -issuer"],
        capture_output=True, timeout=15)
    return r.stdout.decode(errors='replace').strip()

print("== 证书 issuer (httpbin.org) ==")
try:
    print(" ", cert())
except Exception as e:
    print("  ERR", e)

print("== 请求矩阵 ==")
print(req("/anything", "path1"))
print(req("/anything", "path2"))
print(req("/anything/", "trail"))
print(req("/headers", "headers"))
print(req("/anything?x=1", "query"))
print(req("/", "root"))
