# -*- coding: utf-8 -*-
"""在指定 sandbox 上注入并运行 guest 脚本 (参数: sid|new [guest.py] [network])"""
import base64, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vercel_driver import api, cmd, fresh_sandbox

sid = sys.argv[1] if len(sys.argv) > 1 else None
GUEST = sys.argv[2] if len(sys.argv) > 2 else "host_probe_guest3.py"
NET = sys.argv[3] if len(sys.argv) > 3 else "allow-all"
HERE = os.path.dirname(os.path.abspath(__file__))

# 从 guest 源码提取 MARKER 和输出文件名
_src = open(os.path.join(HERE, GUEST), encoding="utf-8").read()
import re as _re
_m = _re.search(r"([A-Z0-9_]+_DONE)", _src)
MARKER = _m.group(1) if _m else "DONE"
_out = _re.search(r"OUT = '([^']+)'", _src)
OUTNAME = _out.group(1).rsplit("/", 1)[-1] if _out else "guest.out"
print("guest=%s marker=%s out=%s" % (GUEST, MARKER, OUTNAME), flush=True)

if sid in (None, 'new'):
    if NET == "deny-all":
        api("DELETE", "/v2/sandboxes/hostprobeh?teamId=%s&projectId=%s" % (__import__("vercel_driver").TEAM, __import__("vercel_driver").PROJ))
        time.sleep(2)
        body = {"projectId": __import__("vercel_driver").PROJ, "name": "hostprobeh",
                "networkPolicy": {"mode": "deny-all"}}
        c, r = api("POST", "/v2/sandboxes?teamId=%s" % __import__("vercel_driver").TEAM, body)
        print("create-deny:", c, r[:300], flush=True)
        if c != 200:
            raise RuntimeError("create failed: %s" % r[:300])
        sid = json.loads(r)["sandbox"]["currentSessionId"]
    else:
        sid = fresh_sandbox("hostprobe" + GUEST[-5], network_mode=NET)
    print("fresh sid:", sid, flush=True)

code = open(os.path.join(HERE, GUEST), "rb").read()
payload = base64.b64encode(code).decode()
inject = "import base64;open('/vercel/sandbox/hp.py','wb').write(base64.b64decode('%s'))" % payload
c, r = cmd(sid, "python3", ["-c", inject], timeout_ms=30000)
print("inject:", c, r[:200], flush=True)
time.sleep(1)
c, r = cmd(sid, "python3", ["/vercel/sandbox/hp.py"], timeout_ms=180000)
print("run:", c, flush=True)
if c == 200:
    print(r[:400], flush=True)
for attempt in range(6):
    time.sleep(2)
    c, r = cmd(sid, "cat", ["/vercel/sandbox/" + OUTNAME], timeout_ms=30000)
    if c == 200 and MARKER in r:
        print("=== 结果 ===", flush=True)
        print(r, flush=True)
        sys.exit(0)
    print("attempt %d status=%d" % (attempt, c), flush=True)
c, r = cmd(sid, "cat", ["/vercel/sandbox/" + OUTNAME], timeout_ms=30000)
print("=== 最后结果 ===", flush=True)
print(r, flush=True)
