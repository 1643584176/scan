# 实验J18: 普通 cmd 进程能力基线侦察(对比 J17 全 caps Spawn 进程)
# 目标: 确认普通沙箱进程 caps -> 若受限则 J17 链 = 真实提权
import json, base64, pathlib, time, urllib.request, urllib.error

TOKEN = "vcp_REDACTED_PLACEHOLDER"
TEAM = "team_GIy1SZ444lspqeNbh4r8uAUg"
PROJ = "prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F"

def api(method, path, body=None, timeout=120):
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

def run_cmd(sid, code, label, wait=True, timeout=120):
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

NAME = "expj18"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

RECON = r'''
import os, subprocess
print("=== self status (uid/caps) ===")
for line in open("/proc/self/status"):
    if line.startswith(("Uid:","Gid:","CapInh:","CapPrm:","CapEff:","CapBnd:","CapAmb:","Seccomp:")):
        print(line.strip())
print("=== uname ===")
print(os.uname())
print("=== /dev ===")
try: print(subprocess.run(["ls","-la","/dev/"],capture_output=True,text=True).stdout)
except Exception as e: print("ERR",e)
print("=== /proc/1/root vs / (chroot check) ===")
try:
    a=os.path.realpath("/proc/1/root"); b=os.path.realpath("/")
    print("pid1 root:",a); print("self root:",b); print("same:", a==b)
except Exception as e: print("ERR",e)
print("=== mounts ===")
print(subprocess.run(["mount"],capture_output=True,text=True).stdout[:3000])
print("=== /proc/sys 可写性探针 ===")
for p in ["/proc/sys/kernel/core_pattern","/proc/sys/kernel/panic",
          "/proc/sys/vm/panic_on_oom","/proc/sys/kernel/modules_disabled"]:
    try:
        with open(p,"w") as f: f.write("x")
        print("WRITABLE:",p)
    except Exception as e:
        print("readonly:",p,type(e).__name__)
print("=== cgroup ===")
print(subprocess.run(["ls","-la","/sys/fs/cgroup/"],capture_output=True,text=True).stdout[:2000])
print("=== net ===")
print(subprocess.run(["ip","addr"],capture_output=True,text=True).stdout[:2000])
print("=== pid1 cmdline/env ===")
print(open("/proc/1/cmdline").read().replace("\0"," "))
try: print(open("/proc/1/environ").read().replace("\0","\n")[:2000])
except Exception as e: print("environ ERR",e)
print("=== 容器指示 ===")
for f in ["/.dockerenv","/run/.containerenv","/proc/1/cgroup"]:
    try: print(f, open(f).read()[:500])
    except Exception as e: print(f,"ERR",type(e).__name__)
'''
run_cmd(sid, RECON, "baseline", wait=True, timeout=60000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
