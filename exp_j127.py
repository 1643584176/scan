# 实验J127: 诊断后台扫描未启动的原因 + 检查沙箱状态
import json, time, urllib.request, urllib.error, sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

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

def run_cmd(sid, code, label, wait=True, timeout=120, args=None, logs=True):
    body = {"command": "python3", "args": (args or ["-c", code]),
            "wait": wait, "logs": logs, "timeout": timeout}
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

# 检查沙箱列表, 找 expj125/126
c, r = api("GET", f"/v2/sandboxes?project={PROJ}&teamId={TEAM}")
print("list:", c, flush=True)
if c == 200:
    data = json.loads(r)
    for sb in data.get("sandboxes", []):
        print("SB:", sb.get("name"), sb.get("currentSessionId"), flush=True)
        # 找最近的 expj126
        if sb.get("name") == "expj125":
            sid = sb.get("currentSessionId")
            print("FOUND expj126 sid:", sid, flush=True)
            # 检查 scan 文件
            for chk in [
                "ls -la /root/ 2>&1",
                "cat /root/launch.log 2>&1",
                "ps aux 2>&1 | grep -v grep | head -20",
                "wc -l /root/scan_out.txt 2>&1; tail -5 /root/scan_out.txt 2>&1",
            ]:
                body = {"command": "sh", "args": ["-c", chk], "wait": True, "logs": True, "timeout": 120}
                cc, rr = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
                print(f"\n-- [{chk[:40]}] status {cc} --", flush=True)
                if cc != 200:
                    print(rr[:300], flush=True)
                    continue
                for line in rr.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        d = json.loads(line)
                        if d.get("stream") in ("stdout", "stderr"):
                            print(d.get("data", ""), end="", flush=True)
                    except Exception:
                        print(line[:300], flush=True)
            break

print("\ndone", flush=True)
