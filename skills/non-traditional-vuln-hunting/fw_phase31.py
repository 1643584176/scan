# -*- coding: utf-8 -*-
"""Phase31: 内网接口端口扫描(172.31.0.2/100.64.0.1) + CA 证书 + /dev 设备检查"""
import sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM

SID = "sbx_9efDIoJf3GAsZlyPJy9MQm6k9MMO"  # fwtest13 (deny-all, 需要 custom 才能连接层放行)

GUEST = r'''
import socket, os, time

# 1) CA 证书内容
for p in ['/etc/pki/ca-trust/source/anchors/vercel-proxy-ca.pem',
          '/usr/local/share/ca-certificates/vercel-proxy-ca.crt']:
    try:
        print('[CA %s] %s' % (p, open(p).read()[:1200]), flush=True)
    except Exception as e:
        print('[CA %s] ERR %s' % (p, e), flush=True)

# 2) /dev 设备号检查 (host 设备 254:0 是否暴露)
try:
    for d in os.listdir('/dev'):
        try:
            st = os.stat('/dev/' + d)
            if st.st_rdev:
                print('[dev %s] %d:%d' % (d, os.major(st.st_rdev), os.minor(st.st_rdev)), flush=True)
        except Exception:
            pass
except Exception as e:
    print('[dev] ERR %s' % e, flush=True)

# 3) fib_trie 看共享 netns 的接口 IP
try:
    print('[fib_trie]', open('/proc/net/fib_trie').read()[:2000], flush=True)
except Exception as e:
    print('[fib_trie] ERR %s' % e, flush=True)

# 4) 内网接口端口扫描
def scan(ip, ports, label=''):
    open_ports = []
    for p in ports:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.2)
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
code = "cat > /tmp/pg39.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg39.py"

if __name__ == "__main__":
    # 切换 custom 策略 (连接层放行) - 用白名单域名规则保持可控
    body = {"allowedDomains": ["webhook.site"]}
    c, r = api("POST", "/v2/sandboxes/sessions/%s/network-policy?teamId=%s" % (SID, TEAM), body)
    print('set custom:', c, r[:200], flush=True)
    time.sleep(2)
    c, r = cmd(SID, "bash", ["-lc", code], timeout_ms=120000)
    print('cmd:', c, flush=True)
    print(r[:12000], flush=True)
