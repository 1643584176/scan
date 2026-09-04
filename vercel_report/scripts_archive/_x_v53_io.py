# -*- coding: utf-8 -*-
"""v53f: /dev/port ioport 补测 (v53b 因 xxd 缺失未出数) + 收尾验证"""
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
    api_raw('DELETE', '/v2/sandboxes/io53?teamId=%s&projectId=%s' % (TEAM, PROJ))
    time.sleep(2)
    c, r = api_raw('POST', '/v4/sandboxes?teamId=%s' % TEAM, {"projectId": PROJ, "name": 'io53'})
    if c != 200:
        print('create failed', r[:200], flush=True)
        sys.exit(1)
    sid = json.loads(r)['sandbox']['currentSessionId']
    print('sid =', sid, flush=True)
    time.sleep(8)

    probe = r'''
python3 - <<'EOF'
import os
def rdport(port,n=1):
    try:
        f=os.open('/dev/port',os.O_RDONLY); os.lseek(f,port,0)
        d=os.read(f,n); os.close(f); return d
    except Exception as e:
        return 'ERR %s' % str(e)[:50]
def wrport(port,d):
    try:
        f=os.open('/dev/port',os.O_RDWR); os.lseek(f,port,0)
        os.write(f,d); os.close(f); return True
    except Exception as e:
        return 'ERR %s' % str(e)[:50]
print('===== 1. 读标准 ioport =====')
for p in [0x70,0x71,0x80,0x61,0xcf8,0xcfc,0x3f8,0x3f9,0x60,0x64,0x2e,0x4d0,0xcd6,0xcd7]:
    print('io %03x: %s' % (p, rdport(p).hex(' ') if isinstance(rdport(p),bytes) else rdport(p)))
print('===== 2. RTC 索引读 (0x70=0, 0x71=秒) ======')
print('wr 0x70<-0:', wrport(0x70,b'\x00'))
print('rd 0x71:', rdport(0x71).hex(' '))
print('wr 0x70<-2:', wrport(0x70,b'\x02'))
print('rd 0x71:', rdport(0x71).hex(' '))
print('===== 3. ioport 全空间扫描 (找非 0xff 端口) =====')
found=[]
for p in range(0,0x4000,16):
    d=rdport(p,1)
    if isinstance(d,bytes) and d!=b'\xff':
        found.append('%03x=%02x' % (p,d[0]))
print('非 0xff 端口: %s' % (' '.join(found) if found else 'NONE'))
print('===== 4. 写测试 0x80 (无副作用) =====')
print('wr rc:', wrport(0x80,b'\x5a'))
print('rd 0x80:', rdport(0x80).hex(' '))
EOF
'''
    b64 = base64.b64encode(probe.encode()).decode()
    c2, r2 = api_raw('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
                     {"command": "bash", "args": ["-c", 'echo %s | base64 -d | bash' % b64],
                      "wait": True, "logs": True, "timeout": 60000}, timeout=150)
    print('[io] -> %d' % c2, flush=True)
    print(parse_data(r2), flush=True)
    api_raw('DELETE', '/v2/sandboxes/io53?teamId=%s&projectId=%s' % (TEAM, PROJ))
    print('DONE', flush=True)
