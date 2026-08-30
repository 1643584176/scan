# -*- coding: utf-8 -*-
"""v53a: guest 内 virtio/PCI/内存设备完整枚举 (基线先行)
枚举: virtio 设备集 / PCI / /proc/iomem / 块设备 / vsock / dmesg
目的: 找标准 Firecracker 设备集之外的额外设备"""
import base64, json, sys, time, urllib.request, urllib.error
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TOKEN, TEAM, PROJ

def api_raw(method, path, body=None, timeout=180, maxlen=200000):
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
    api_raw('DELETE', '/v2/sandboxes/enum53?teamId=%s&projectId=%s' % (TEAM, PROJ))
    time.sleep(2)
    c, r = api_raw('POST', '/v4/sandboxes?teamId=%s' % TEAM, {"projectId": PROJ, "name": 'enum53'})
    if c != 200:
        print('create failed', r[:200], flush=True)
        sys.exit(1)
    sid = json.loads(r)['sandbox']['currentSessionId']
    print('sid =', sid, flush=True)
    time.sleep(8)

    probe = r'''
echo "===== 1. /sys/bus/virtio/devices ====="
for d in /sys/bus/virtio/devices/*; do
  [ -e "$d" ] || continue
  echo "--- $d"
  cat $d/uevent 2>/dev/null
  ls -l $d/driver 2>/dev/null | sed 's/.*driver -> //'
done
echo "===== 2. virtio drivers ====="
ls /sys/bus/virtio/drivers/ 2>/dev/null
echo "===== 3. PCI devices ====="
lspci -vvv 2>/dev/null | head -80 || ls /sys/bus/pci/devices/ 2>/dev/null
echo "===== 4. /proc/iomem ====="
cat /proc/iomem 2>/dev/null
echo "===== 5. /dev 设备节点 ====="
ls -la /dev/ 2>/dev/null | grep -vE '^(total|d)' | head -60
echo "===== 6. /proc/partitions + block size ====="
cat /proc/partitions 2>/dev/null
for b in /sys/block/*; do
  echo "$b: $(cat $b/size 2>/dev/null) sectors $(cat $b/device/model 2>/dev/null)"
done
echo "===== 7. vsock ====="
ls -la /dev/vsock 2>/dev/null; cat /sys/class/vsock/*/* 2>/dev/null | head
echo "===== 8. dmesg virtio/pci/block ====="
dmesg 2>/dev/null | grep -iE 'virtio|pci|scsi|vda|vdb|block|mmio' | head -40
echo "===== 9. /proc/devices ====="
cat /proc/devices 2>/dev/null
echo "===== 10. mounts ====="
mount | head -25
'''
    b64 = base64.b64encode(probe.encode()).decode()
    c2, r2 = api_raw('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
                     {"command": "bash", "args": ["-c", 'echo %s | base64 -d | bash' % b64],
                      "wait": True, "logs": True, "timeout": 60000}, timeout=150)
    print('[enum] -> %d' % c2, flush=True)
    print(parse_data(r2), flush=True)
    api_raw('DELETE', '/v2/sandboxes/enum53?teamId=%s&projectId=%s' % (TEAM, PROJ))
    print('DONE', flush=True)
