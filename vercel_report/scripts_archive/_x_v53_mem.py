# -*- coding: utf-8 -*-
"""v53b: 内存设备面深入 — /dev/mem 行为 / 空洞映射 / ACPI dump / virtio-mmio 寄存器 / MSR
基线: 标准 5 设备 (blk x2 + net + vsock + rng), pci=off, 无额外 virtio"""
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
    api_raw('DELETE', '/v2/sandboxes/mem53?teamId=%s&projectId=%s' % (TEAM, PROJ))
    time.sleep(2)
    c, r = api_raw('POST', '/v4/sandboxes?teamId=%s' % TEAM, {"projectId": PROJ, "name": 'mem53'})
    if c != 200:
        print('create failed', r[:200], flush=True)
        sys.exit(1)
    sid = json.loads(r)['sandbox']['currentSessionId']
    print('sid =', sid, flush=True)
    time.sleep(8)

    probe = r'''
echo "===== 1. /dev/cpu/0/msr ====="
ls -la /dev/cpu/0/ 2>/dev/null
if [ -e /dev/cpu/0/msr ]; then
  python3 - <<'EOF' 2>&1 || echo "no python3"
import os
for name, idx in [("EFER",0xC0000080),("LSTAR",0xC0000082),("STAR",0xC0000081),("SYSCFG",0xC0010010),("SYSENTER_EIP",0x175)]:
    try:
        fd = os.open('/dev/cpu/0/msr', os.O_RDONLY)
        os.lseek(fd, idx, 0)
        v = os.read(fd, 8)
        os.close(fd)
        print(name, idx, hex(int.from_bytes(v,'little')))
    except Exception as e:
        print(name, idx, 'ERR', str(e)[:80])
EOF
fi
echo "===== 2. /dev/mem 读写行为 ====="
rdmem() {  # addr n
  dd if=/dev/mem bs=1 count=$2 skip=$1 2>/dev/null | xxd -p
  echo "  <- 0x$(printf %x $1) rc=${PIPESTATUS[0]}"
}
echo "-- 设备区 virtio0 寄存器 0xc0001000 (应可读: 非RAM)"
rdmem $((0xc0001000)) 16
echo "-- System RAM 内核代码区 0x100000 (STRICT_DEVMEM 应拒绝)"
rdmem $((0x100000)) 16
echo "-- System RAM 低端 0x10000000 (应拒绝)"
rdmem $((0x10000000)) 16
echo "-- 空洞 0xd0000000 (available for PCI devices)"
rdmem $((0xd0000000)) 16
echo "-- 空洞 0xe0000000"
rdmem $((0xe0000000)) 16
echo "-- 空洞 0xc0000000 (设备区起点下沿)"
rdmem $((0xc0000000)) 16
echo "-- high RAM 之上 0x156d0000 (RAM 结束 0x156cfffff)"
rdmem $((0x156d0000)) 16
echo "-- high RAM 区 0x100000000 (应拒绝)"
rdmem $((0x100000000)) 16
echo "-- RAM 顶部 0xbffff000 (应拒绝)"
rdmem $((0xbffff000)) 16
echo "-- 设备区最后一个 0xc0005000 (rng)"
rdmem $((0xc0005000)) 16
echo "-- 设备区之后 0xc0006000 (无设备)"
rdmem $((0xc0006000)) 16
echo "===== 3. /dev/port ioport ====="
rdport() { dd if=/dev/port bs=1 count=$2 skip=$1 2>/dev/null | xxd -p; echo "  <- io 0x$(printf %x $1) rc=${PIPESTATUS[0]}"; }
echo "-- RTC 0x70/0x71"
rdport $((0x70)) 1
rdport $((0x71)) 1
echo "-- PCI config 0xcf8 (pci=off 但试试)"
rdport $((0xcf8)) 4
echo "-- 0x80 debug port"
rdport $((0x80)) 1
echo "-- 0x61 PPI"
rdport $((0x61)) 1
echo "===== 4. ACPI 表 ====="
ls -la /sys/firmware/acpi/tables/ 2>/dev/null
for t in DSDT FACP APIC SSDT HPET MCFG; do
  f=/sys/firmware/acpi/tables/$t
  [ -f "$f" ] && echo "--- $t $(stat -c%s $f) bytes: $(dd if=$f bs=1 count=16 2>/dev/null | xxd -p)"
done
echo "-- DSDT 内设备名 (strings)"
cat /sys/firmware/acpi/tables/DSDT 2>/dev/null | strings -n 4 | head -40
echo "-- FACP dump (前 64B)"
dd if=/sys/firmware/acpi/tables/FACP bs=1 count=64 2>/dev/null | xxd
echo "===== 5. virtio-mmio 寄存器 dump ====="
for a in c0001000 c0002000 c0003000 c0004000 c0005000; do
  echo "--- 0x$a"
  dd if=/dev/mem bs=4 count=16 skip=$((0x$a/4)) 2>/dev/null | xxd -p | tr -d '\n'; echo
done
echo "===== 6. /sys/firmware 目录 ====="
find /sys/firmware -maxdepth 2 2>/dev/null | head -30
echo "===== 7. dmesg balloon/console/mem ====="
dmesg 2>/dev/null | grep -iE 'balloon|console|acpi|LNRO' | head -20
echo "===== 8. iomem 完整再确认 ====="
cat /proc/iomem
'''
    b64 = base64.b64encode(probe.encode()).decode()
    c2, r2 = api_raw('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
                     {"command": "bash", "args": ["-c", 'echo %s | base64 -d | bash' % b64],
                      "wait": True, "logs": True, "timeout": 60000}, timeout=150)
    print('[mem] -> %d' % c2, flush=True)
    print(parse_data(r2), flush=True)
    api_raw('DELETE', '/v2/sandboxes/mem53?teamId=%s&projectId=%s' % (TEAM, PROJ))
    print('DONE', flush=True)
