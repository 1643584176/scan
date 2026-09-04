# -*- coding: utf-8 -*-
"""v53e: VMCLOCK 长观察 — 11s 内 seq/时钟字段是否被 host 更新 + 写后覆盖观察"""
import base64, json, sys, time, urllib.request, urllib.error
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TOKEN, TEAM, PROJ

def api_raw(method, path, body=None, timeout=180, maxlen=400000):
    req = urllib.request.Request('https://api.vercel.com' + path, method=method)
    req.add_header('Authorization', 'Bearer ' + TOKEN)
    req.add_header('Content-Type', 'application/json')
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
            return r.status, r.read().decode(errors='replace')[:maxlen]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors='replace')[:maxlen]
    except Exception as e:
        return -1, 'EXC %s' % str(e)[:120]

def parse_data(r):
    out = ''
    for line in r.splitlines():
        if '"data"' in line:
            try:
                out += json.loads(line).get('data', '')
            except Exception:
                pass
    return out

if __name__ == '__main__':
    api_raw('DELETE', '/v2/sandboxes/obs53?teamId=%s&projectId=%s' % (TEAM, PROJ))
    time.sleep(2)
    c, r = api_raw('POST', '/v4/sandboxes?teamId=%s' % TEAM, {"projectId": PROJ, "name": 'obs53'})
    if c != 200:
        print('create failed', r[:200], flush=True)
        sys.exit(1)
    sid = json.loads(r)['sandbox']['currentSessionId']
    print('sid =', sid, flush=True)
    time.sleep(8)

    probe = r'''
python3 - <<'EOF'
import os, time
def rd(addr,n=64):
    try:
        f=os.open('/dev/mem',os.O_RDONLY); os.lseek(f,addr,0)
        d=os.read(f,n); os.close(f); return d
    except Exception as e:
        return None
base=0xde000
prev=None
for i in range(11):
    d=rd(base,64)
    if d is None: print('ERR'); break
    vals=[int.from_bytes(d[j:j+4],'little') for j in range(0,64,4)]
    tag=''
    if prev is not None:
        diffs=[k for k in range(16) if vals[k]!=prev[k]]
        if diffs: tag=' DIFF@'+','.join('%02x'%(k*4) for k in diffs)
    print('t=%2ds %s%s' % (i, ' '.join('%08x'%v for v in vals), tag))
    prev=vals
    time.sleep(1)
print('-- 写 +0x10=0xdeadbeef 后观察 3s (host 覆盖?)')
f=os.open('/dev/mem',os.O_RDWR); os.lseek(f,base+0x10,0); os.write(f,b'\xef\xbe\xad\xde'); os.close(f)
for i in range(4):
    d=rd(base+0x10,4)
    print('  +%ds: %s' % (i, d.hex(' ') if d else 'ERR'))
    time.sleep(1)
EOF
'''
    b64 = base64.b64encode(probe.encode()).decode()
    c2, r2 = api_raw('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
                     {"command": "bash", "args": ["-c", 'echo %s | base64 -d | bash' % b64],
                      "wait": True, "logs": True, "timeout": 60000}, timeout=150)
    print('[obs] -> %d' % c2, flush=True)
    print(parse_data(r2), flush=True)
    api_raw('DELETE', '/v2/sandboxes/obs53?teamId=%s&projectId=%s' % (TEAM, PROJ))
    print('DONE', flush=True)
