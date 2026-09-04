# -*- coding: utf-8 -*-
"""v53c: AMZNC10C ACPI 设备深挖 + 空洞读回数据 + ACPI 表 dump
发现: iomem Reserved 0xde000-0xdefff = AMZNC10C:00 (AWS Nitro 设备名, 非标准 Firecracker DSDT 内容)
目标: DSDT 全文 / 该 MMIO 是否 host 响应 / MCFG-APIC dump / memmap"""
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
    api_raw('DELETE', '/v2/sandboxes/acpi53?teamId=%s&projectId=%s' % (TEAM, PROJ))
    time.sleep(2)
    c, r = api_raw('POST', '/v4/sandboxes?teamId=%s' % TEAM, {"projectId": PROJ, "name": 'acpi53'})
    if c != 200:
        print('create failed', r[:200], flush=True)
        sys.exit(1)
    sid = json.loads(r)['sandbox']['currentSessionId']
    print('sid =', sid, flush=True)
    time.sleep(8)

    probe = r'''
echo "===== 1. DSDT 全文 hex+ascii ====="
python3 - <<'EOF'
import os
p='/sys/firmware/acpi/tables/DSDT'
d=open(p,'rb').read()
print('DSDT len', len(d))
print('HEX:')
for i in range(0,len(d),16):
    print('%04x  %s  %s' % (i, d[i:i+16].hex(' '), ''.join(chr(c) if 32<=c<127 else '.' for c in d[i:i+16])))
EOF
echo "===== 2. MCFG/APIC/FACP hex ====="
python3 - <<'EOF'
for t in ['MCFG','APIC','FACP']:
    try:
        d=open('/sys/firmware/acpi/tables/'+t,'rb').read()
        print('---',t,len(d))
        for i in range(0,len(d),16):
            print('%04x  %s' % (i, d[i:i+16].hex(' ')))
    except Exception as e:
        print(t,'ERR',e)
EOF
echo "===== 3. /dev/mem 各区域读回数据 ====="
python3 - <<'EOF'
import os
def rd(addr,n=32):
    try:
        f=os.open('/dev/mem',os.O_RDONLY)
        os.lseek(f,addr,0)
        d=os.read(f,n)
        os.close(f)
        print('0x%08x: %s' % (addr, d.hex(' ')))
    except Exception as e:
        print('0x%08x: ERR %s' % (addr, str(e)[:60]))
print('-- AMZNC10C 区 0xde000 (4KB, 读前 64B)')
rd(0xde000,64)
print('-- AMZNC10C 区 0xde000 尾部 0xdeff0')
rd(0xdeff0,16)
print('-- 空洞 0xc0000000')
rd(0xc0000000,32)
print('-- virtio0 基线 0xc0001000')
rd(0xc0001000,32)
print('-- 空洞 0xd0000000')
rd(0xd0000000,32)
print('-- 空洞 0xe0000000')
rd(0xe0000000,32)
print('-- 设备区后 0xc0006000')
rd(0xc0006000,32)
print('-- RAM 应拒 0x100000')
rd(0x100000,16)
print('-- high RAM 应拒 0x100000000')
rd(0x100000000,16)
print('-- iomem Reserved 0x9fc00')
rd(0x9fc00,32)
print('-- 低端 0xe0000 (RSDP 区)')
rd(0xe0000,16)
EOF
echo "===== 4. /sys/bus/acpi/devices 枚举 ====="
for d in /sys/bus/acpi/devices/*; do
  echo "--- $d"
  cat $d/path 2>/dev/null
  cat $d/status 2>/dev/null
  ls $d/ 2>/dev/null | head -10
done
echo "===== 5. dmesg amzn/nitro ====="
dmesg 2>/dev/null | grep -iE 'amzn|nitro|c10c|LNRO|virtio-mmio' | head -20
echo "===== 6. /sys/firmware/memmap ====="
for m in /sys/firmware/memmap/*; do
  echo "$m: $(cat $m/start 2>/dev/null)-$(cat $m/end 2>/dev/null) $(cat $m/type 2>/dev/null)"
done
echo "===== 7. /sys/devices 顶层 ====="
ls /sys/devices/ 2>/dev/null
echo "===== 8. /sys/bus/platform/devices ====="
ls -la /sys/bus/platform/devices/ 2>/dev/null | head -20
'''
    b64 = base64.b64encode(probe.encode()).decode()
    c2, r2 = api_raw('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
                     {"command": "bash", "args": ["-c", 'echo %s | base64 -d | bash' % b64],
                      "wait": True, "logs": True, "timeout": 60000}, timeout=150)
    print('[acpi] -> %d' % c2, flush=True)
    print(parse_data(r2), flush=True)
    api_raw('DELETE', '/v2/sandboxes/acpi53?teamId=%s&projectId=%s' % (TEAM, PROJ))
    print('DONE', flush=True)
