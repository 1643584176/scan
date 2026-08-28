# -*- coding: utf-8 -*-
"""Phase20: 特殊运行时防火墙差异 + forwardURL https 本机/内网 + image 格式"""
import sys, time, re, json
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM, PROJ

GUEST = r'''
import socket, struct, time
def probe(ip, port, label=''):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        t0 = time.time()
        s.connect((ip, port))
        print('[%s %s:%d] CONNECT OK %.2fs' % (label, ip, port, time.time()-t0), flush=True)
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
# deny-all 下各面
probe('34.195.135.204', 443, 'np-443')
probe('34.195.135.204', 5432, 'np-5432')
pg('34.195.135.204', 5432)
probe('169.254.169.254', 80, 'meta')
probe('172.31.0.2', 53, 'dns53')
probe('178.63.67.153', 80, 'wh-80')
# UDP
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
code = "cat > /tmp/pg28.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg28.py"

if __name__ == "__main__":
    # 1) 拿完整 runtime 枚举
    body = {"projectId": PROJ, "name": "fwtestR", "networkPolicy": {"mode": "deny-all"}, "runtime": "xxx"}
    c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM, body)
    print('runtime enum err:', r[:600], flush=True)

    # 2) 特殊运行时 + deny-all 出网行为
    for rt in ['cua-ubuntu-xfce', 'walleye-python', 'blackbox-playwright']:
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
        # 清理
        api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % ("fwtestR", TEAM, PROJ))
        time.sleep(1)
