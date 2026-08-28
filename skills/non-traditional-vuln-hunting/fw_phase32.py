# -*- coding: utf-8 -*-
"""Phase32: /dev/vda+/dev/mem+/dev/kmsg 可读性测试 + custom 下内网端口扫描"""
import sys, time, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM

SID = "sbx_9efDIoJf3GAsZlyPJy9MQm6k9MMO"  # fwtest13

GUEST = r'''
import os, socket

# 1) 设备可读性测试 (只读, 不写!)
def try_read(path, off, size=64, label=''):
    try:
        fd = os.open(path, os.O_RDONLY)
        try:
            data = os.pread(fd, size, off)
            print('[%s %s@%d] OK %r' % (label, path, off, data[:64]), flush=True)
        finally:
            os.close(fd)
    except Exception as e:
        print('[%s %s@%d] EXC %s' % (label, path, off, e), flush=True)

try_read('/dev/vda', 0, 512, 'vda')
try_read('/dev/vda', 0x100000, 512, 'vda')
try_read('/dev/mem', 0, 64, 'mem')
try_read('/dev/mem', 0x100000, 64, 'mem')
try_read('/dev/kmsg', 0, 2048, 'kmsg')
try_read('/dev/snapshot', 0, 64, 'snapshot')

# 2) 块设备大小 (ioctl BLKGETSIZE64 = 0x80081272)
try:
    import fcntl, struct
    fd = os.open('/dev/vda', os.O_RDONLY)
    sz = fcntl.ioctl(fd, 0x80081272, struct.pack('Q', 0))
    print('[vda-size] %d bytes = %.1f GB' % (struct.unpack('Q', sz)[0], struct.unpack('Q', sz)[0] / 1e9), flush=True)
    os.close(fd)
except Exception as e:
    print('[vda-size] EXC %s' % e, flush=True)

# 3) cgroup 设备控制器状态
try:
    print('[cgroup]', open('/sys/fs/cgroup/cgroup.controllers').read(), flush=True)
    print('[cgroup-sub]', open('/sys/fs/cgroup/cgroup.subtree_control').read(), flush=True)
except Exception as e:
    print('[cgroup] ERR %s' % e, flush=True)

# 4) 内网端口扫描 (custom 下连接层放行)
def scan(ip, ports, label=''):
    open_ports = []
    for p in ports:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.0)
        try:
            if s.connect_ex((ip, p)) == 0:
                open_ports.append(p)
        except Exception:
            pass
        s.close()
    print('[scan %s] open: %s' % (label, open_ports), flush=True)

ports = [22, 53, 80, 443, 2375, 2376, 3000, 4000, 5000, 5432, 6379, 8000, 8080,
         8443, 8888, 9000, 9090, 10000, 10250, 23456, 30000, 50000, 65534]
scan('172.31.0.2', ports, 'dns-172.31.0.2')
scan('100.64.0.1', ports, 'gw-100.64.0.1')
scan('169.254.169.254', ports[:16], 'metadata')
print('done', flush=True)
'''
code = "cat > /tmp/pg40.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg40.py"

if __name__ == "__main__":
    # 正确的 custom 格式
    body = {"mode": "custom", "allowedDomains": ["webhook.site"]}
    c, r = api("POST", "/v2/sandboxes/sessions/%s/network-policy?teamId=%s" % (SID, TEAM), body)
    print('set custom:', c, r[:300], flush=True)
    time.sleep(2)
    c, r = cmd(SID, "bash", ["-lc", code], timeout_ms=120000)
    print('cmd:', c, flush=True)
    print(r[:10000], flush=True)
