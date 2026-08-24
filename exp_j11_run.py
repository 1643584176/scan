# 实验J10驱动: 观察线程(100s) + 并发大payload cmd 循环触发 agent 请求
import json, base64, pathlib, time, threading, urllib.request, urllib.error

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

def run_cmd(sid, code, label, timeout=120):
    body = {"command": "python3", "args": ["-c", code],
            "wait": True, "logs": True, "timeout": timeout}
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
    print(f"=== cmd[{label}] status {c} ===", flush=True)
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

NAME = "expj11"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

# cmd A: 观察脚本(100s) - 放线程里跑
payload = base64.b64encode(pathlib.Path("exp_j11.py").read_bytes()).decode()
code_a = f"import base64;exec(base64.b64decode('{payload}').decode())"
ta = threading.Thread(target=run_cmd, args=(sid, code_a, "observer", 150000), daemon=True)
ta.start()
print(">>> observer 已启动, sleep 5 等观察线程就绪", flush=True)
time.sleep(5)

# 触发循环: 大 payload cmd(放大 SpawnRequest body)
pad = "A" * (200 * 1024)
for i in range(15):
    code_t = f"import os;print('TRIG{i}', os.getpid());print('{pad[:1000]}...' if False else 'ok')"
    # 真正的大 payload: 直接嵌 200KB 字符串到 code 里
    code_t = f"x = '{pad}'; print('TRIG{i}', len(x), x[:10])"
    run_cmd(sid, code_t, f"trig{i}", timeout=60)
    time.sleep(0.5)

ta.join(timeout=160)
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
