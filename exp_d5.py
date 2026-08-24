# 实验D5: Firecracker MMDS 完整探测
# 1) 获取 IMDSv2 token
# 2) 遍历元数据树 (meta-data / dynamic / user-data / network)
# 3) Firecracker API 行为
import subprocess, urllib.request, urllib.error, json

BASE = "http://169.254.169.254"

def run(cmd, timeout=10):
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, timeout=timeout)
        return r.stdout.decode(errors='replace') + r.stderr.decode(errors='replace')
    except Exception as e:
        return f"ERR {e}"

def get_token():
    try:
        req = urllib.request.Request(f"{BASE}/latest/api/token", method="PUT")
        req.add_header("X-aws-ec2-metadata-token-ttl-seconds", "21600")
        with urllib.request.urlopen(req, timeout=8) as r:
            return r.read().decode().strip()
    except Exception as e:
        return None

def get(path, token=None):
    try:
        req = urllib.request.Request(f"{BASE}{path}")
        if token:
            req.add_header("X-aws-ec2-metadata-token", token)
        with urllib.request.urlopen(req, timeout=8) as r:
            return r.status, r.read().decode(errors='replace')[:800]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors='replace')[:300]
    except Exception as e:
        return -1, f"{type(e).__name__}:{e}"

print("== [1] 获取 token ==")
tok = get_token()
print("   token:", (tok or "FAILED")[:60], "..." if tok else "")

print("== [2] 元数据树遍历 ==")
paths = [
    "/latest/meta-data/",
    "/latest/meta-data/iam/",
    "/latest/meta-data/iam/security-credentials/",
    "/latest/meta-data/iam/security-credentials/role",
    "/latest/meta-data/instance-id",
    "/latest/meta-data/local-ipv4",
    "/latest/meta-data/public-ipv4",
    "/latest/meta-data/hostname",
    "/latest/meta-data/placement/",
    "/latest/meta-data/network/",
    "/latest/dynamic/",
    "/latest/user-data",
    "/latest/",
    "/",
    "/meta-data/",
]
for p in paths:
    c, r = get(p, tok)
    print(f"  {p:<55} -> {c} {r[:150]}")

print("== [3] Firecracker API 探测 ==")
print("   mmds 端点:", get("/mmds", tok))
print("   v1 API:", get("/v1/", tok))
print("   options:", run(f"curl -s -i -X OPTIONS {BASE}/ 2>&1 | head -8"))
print("   any-api:", get("/latest/meta-data/placement/availability-zone", tok))
