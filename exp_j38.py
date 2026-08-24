# 实验J38: init.sock 通信面侦察 - /run/vercel/share 共享挂载暴露的 socket
# 目标: 确认 socket 监听者(沙箱内 sandbox-init vs 宿主进程), 协议线索, 可连接性
import json, time, urllib.request, urllib.error, sys
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
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
    print(f"=== cmd[{label}] status {c} ===", flush=True)
    if c != 200:
        print(f"  RAW: {r[:400]}", flush=True)
        return
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

NAME = "expj38"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

SCAN = r'''
import os, socket, subprocess, time, glob

print("===== [1] /run/vercel/share 内容 =====", flush=True)
for p in sorted(glob.glob("/run/vercel/share/*")):
    st = os.stat(p)
    print("%s mode=%o size=%d uid=%d gid=%d" % (p, st.st_mode, st.st_size, st.st_uid, st.st_gid), flush=True)
    if os.path.islink(p):
        print("  -> symlink:", os.readlink(p), flush=True)

print("===== [2] 进程列表 =====", flush=True)
print(subprocess.run(["ps", "aux"], capture_output=True, text=True).stdout, flush=True)

print("===== [3] /proc/net/unix (socket 列表) =====", flush=True)
print(open("/proc/net/unix").read(), flush=True)

print("===== [4] 尝试连接 init.sock =====", flush=True)
for path in ["/run/vercel/share/init.sock", "/run/vercel/share/init.sock1"]:
    if not os.path.exists(path):
        print("%s: NOT EXISTS" % path, flush=True)
        continue
    st = os.stat(path)
    print("%s: mode=%o type=%s" % (path, st.st_mode, "socket" if (st.st_mode & 0o170000) == 0o140000 else "other"), flush=True)
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect(path)
        print("CONNECT OK", flush=True)
        try:
            s.settimeout(1)
            data = s.recv(4096)
            print("recv: %r" % data[:400], flush=True)
        except socket.timeout:
            print("no banner (timeout 1s)", flush=True)
        for probe in [b"help\n", b"version\n", b"ping\n", b'{"method":"ping"}\n']:
            try:
                s.settimeout(1.5)
                s.sendall(probe)
                data = s.recv(4096)
                print("probe %r -> %r" % (probe[:40], data[:300]), flush=True)
            except Exception as e:
                print("probe %r -> %s" % (probe[:40], type(e).__name__), flush=True)
        s.close()
    except Exception as e:
        print("connect FAILED: %r" % e, flush=True)

print("===== [5] sandbox-init 二进制静态分析 =====", flush=True)
try:
    b = open("/run/vercel/share/sandbox-init", "rb").read()
    print("binary size:", len(b), flush=True)
    # 可打印字符串
    import re
    strs = re.findall(rb"[\x20-\x7e]{5,}", b)
    print("total strings:", len(strs), flush=True)
    interesting = [s for s in strs if re.search(rb"(sock|rpc|json|cmd|exec|log|init|vercel|api|token|key|auth|read|write|file|shutdown|exit|version|hello|connect|listen)", s, re.I)]
    for s in interesting[:80]:
        print("  %r" % s.decode('latin1'), flush=True)
except Exception as e:
    print("read failed: %r" % e, flush=True)

print("===== [6] 其他 socket 位置扫描 =====", flush=True)
for root in ["/run", "/tmp", "/var/run"]:
    try:
        for dirpath, dirnames, filenames in os.walk(root):
            for fn in filenames:
                fp = os.path.join(dirpath, fn)
                try:
                    st = os.stat(fp)
                    if (st.st_mode & 0o170000) == 0o140000:
                        print("SOCKET: %s mode=%o" % (fp, st.st_mode), flush=True)
                except Exception:
                    pass
    except Exception:
        pass
'''
run_cmd(sid, SCAN, "init-sock-recon", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
