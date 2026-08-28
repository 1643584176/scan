# -*- coding: utf-8 -*-
"""Phase21: python3.13/node24/node26 运行时 deny-all 网络行为 + image 字段格式"""
import sys, time, re, json
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM, PROJ

GUEST = r'''
import socket, struct, time
def probe(ip, port, label=''):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((ip, port))
        print('[%s %s:%d] CONNECT OK' % (label, ip, port), flush=True)
        s.close()
    except Exception as e:
        print('[%s %s:%d] EXC %s' % (label, ip, port, e), flush=True)
def pg(ip, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((ip, port))
        s.sendall(struct.pack('>II', 8, 80877103))
        r = s.recv(1)
        print('[pg %s:%d] resp %r' % (ip, port, r), flush=True)
        s.close()
    except Exception as e:
        print('[pg %s:%d] EXC %s' % (ip, port, e), flush=True)
probe('34.195.135.204', 443, 'np-443')
probe('34.195.135.204', 5432, 'np-5432')
pg('34.195.135.204', 5432)
probe('169.254.169.254', 80, 'meta')
probe('172.31.0.2', 53, 'dns53')
probe('178.63.67.153', 80, 'wh-80')
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(4)
    s.sendto(b'x', ('34.195.135.204', 53))
    r, a = s.recvfrom(100)
    print('[udp-np] resp %r' % r, flush=True)
except Exception as e:
    print('[udp-np] EXC %s' % e, flush=True)
print('done', flush=True)
'''
code = "cat > /tmp/pg29.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg29.py"

if __name__ == "__main__":
    # 1) image 字段格式试探
    print('=== image field formats ===', flush=True)
    for img in ['node22', 'python3.13', 'cua-ubuntu-xfce', 'vercel/node22',
                'node:22', 'library/node', 'vercel-runtimes/node22', 'node22:latest']:
        body = {"projectId": PROJ, "name": "fwtestR", "networkPolicy": {"mode": "deny-all"}, "image": img}
        c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM, body)
        print('[image=%s] -> %d %s' % (img, c, r[:120]), flush=True)
        time.sleep(1)

    # 2) 不同标准运行时 + deny-all 出网
    print('=== runtimes deny-all ===', flush=True)
    for rt in ['python3.13', 'node24', 'node26']:
        body = {"projectId": PROJ, "name": "fwtestR", "networkPolicy": {"mode": "deny-all"}, "runtime": rt}
        c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM, body)
        if c != 200:
            print('[rt=%s] create -> %d %s' % (rt, c, r[:150]), flush=True)
            continue
        try:
            sid = json.loads(r)["sandbox"]["currentSessionId"]
        except Exception as e:
            print('[rt=%s] parse err %s' % (rt, e), flush=True)
            continue
        print('[rt=%s] created %s' % (rt, sid), flush=True)
        time.sleep(2)
        c, r = cmd(sid, "bash", ["-lc", code], timeout_ms=90000)
        outs = re.findall(r'\[(?:np|pg|meta|dns|wh|udp)[^]]*\] [^\x00]{0,200}', r)
        for o in outs:
            print('[rt=%s] %s' % (rt, o), flush=True)
        api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % ("fwtestR", TEAM, PROJ))
        time.sleep(1)
    print('done', flush=True)
