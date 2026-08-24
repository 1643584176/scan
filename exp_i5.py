# 实验I5: sandbox-init ConnectRPC 服务枚举与调用
import subprocess, socket, json

def run(cmd, timeout=30):
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, timeout=timeout)
        return (r.stdout + r.stderr).decode(errors='replace')
    except Exception as e:
        return f"ERR {e}"

print("== [1] 全部 proto 服务/方法 ==")
print(run("grep -a -o -E 'vercel\\.[a-z0-9_.]+\\.[A-Z][A-Za-z0-9]+' /run/vercel/share/sandbox-init 2>/dev/null | sort -u | head -40"))

def connect_call(service_method, body=b"{}", timeout=4):
    """Connect JSON 协议"""
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect("/run/vercel/share/init.sock")
        path = f"/{service_method}"
        hdr = (f"POST {path} HTTP/1.1\r\nHost: localhost\r\n"
               f"Content-Type: application/json\r\n"
               f"Connect-Protocol-Version: 1\r\n"
               f"Content-Length: {len(body)}\r\n\r\n").encode()
        s.sendall(hdr + body)
        data = b""
        try:
            while len(data) < 4000:
                c = s.recv(4096)
                if not c:
                    break
                data += c
        except socket.timeout:
            pass
        s.close()
        return data[:1500]
    except Exception as e:
        return f"ERR {type(e).__name__}: {e}".encode()

methods = ["Spawn", "SpawnStarted", "PtyStart", "PtyResize", "Exec", "Command", "Run",
           "List", "Status", "Info", "Stop", "Kill", "Get", "Set", "Update"]

print("== [2] Connect 协议调用 ==")
for m in methods:
    r = connect_call(f"vercel.sandbox.spawn.v1.SpawnService/{m}")
    if b"404" not in r and b"NO-RESPONSE" not in r:
        print(f"  {m}: {r[:400]!r}", flush=True)

print("== [3] 尝试其他服务名 ==")
for svc in ["vercel.sandbox.v1.SandboxService", "vercel.sandbox.v1.ExecService",
            "vercel.sandbox.v1.ControlService", "vercel.sandbox.v1.AgentService",
            "vercel.sandbox.v1.Sandbox", "vercel.sandbox.v1.Init"]:
    for m in ["Spawn", "Exec", "Status", "Info", "Get", "Run"]:
        r = connect_call(f"{svc}/{m}")
        if b"404" not in r and b"NO-RESPONSE" not in r:
            print(f"  {svc}/{m}: {r[:300]!r}", flush=True)

print("done", flush=True)
