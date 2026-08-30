# -*- coding: utf-8 -*-
"""custom 模式公网裸 IP TCP 数据层测试 (v45b)
D 线发现: custom 下私有网段全放行 (dup #3951926: domain-allow 缺 dest-IP 校验)
今日 UDP 测试意外发现: custom 下 8.8.8.8:53 (公网裸 IP, 不在 allowlist) TCP_OPEN
方法论修正: connect 成功 ≠ 放行 (防火墙模拟握手, deny 在数据层)
补测数据层: 8.8.8.8:53 TCP DNS 查询 / 1.1.1.1:443 TLS ClientHello / 8.8.8.8:9999 黑洞"""
import base64, json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

NAME = 'tcpdata45'

def mk():
    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    time.sleep(3)
    for attempt in range(8):
        c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM,
                   {"projectId": PROJ, "name": NAME, "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}}, 60)
        if c == 429:
            print('[create] 429 retry %d' % (attempt + 1), flush=True)
            time.sleep(20)
            continue
        break
    print('[create] -> %s' % c, flush=True)
    if c != 200:
        sys.exit(1)
    return json.loads(r)['sandbox']['currentSessionId']

def set_policy(sid, mode):
    body = {"mode": mode}
    if mode == 'custom':
        body["allowedDomains"] = ["httpbin.org"]
    c, r = api("POST", "/v2/sandboxes/sessions/%s/network-policy?teamId=%s" % (sid, TEAM), body, 60)
    print('[policy] %s -> %d %s' % (mode, c, (r or '')[:120]), flush=True)
    time.sleep(4)

PROBE = '''import socket, struct, time
def tcp_data(tag, ip, port, payload, t=5):
    s = socket.socket(); s.settimeout(t)
    t0 = time.time()
    try:
        s.connect((ip, port))
        print(tag, ip+':'+str(port), 'CONNECT_OK %.1fs' % (time.time()-t0), flush=True)
        try:
            s.sendall(payload)
            d = s.recv(512)
            print(tag, ip+':'+str(port), 'DATA_RESP %dB %s' % (len(d), d[:16].hex()), flush=True)
        except socket.timeout:
            print(tag, ip+':'+str(port), 'DATA_NORESP %.1fs' % (time.time()-t0), flush=True)
        except Exception as e:
            print(tag, ip+':'+str(port), 'DATA_ERR %s' % e, flush=True)
    except Exception as e:
        print(tag, ip+':'+str(port), 'CONNECT_ERR %s' % e, flush=True)
    finally:
        s.close()

def dns_tcp(name='example.com'):
    tid = 0x2222
    hdr = struct.pack('>HHHHHH', tid, 0x0100, 1, 0, 0, 0)
    q = b''.join(bytes([len(x)]) + x.encode() for x in name.split('.')) + b'\\x00'
    body = hdr + q + struct.pack('>HH', 1, 1)
    return struct.pack('>H', len(body)) + body

tls_hello = bytes.fromhex('16030100c5010000c10303') + b'\\x00' * 32 + b'\\x00' * 28 + b'\\x00\\x00\\x00' + b'\\x00' * 90

tcp_data('dns', '8.8.8.8', 53, dns_tcp())
tcp_data('tls', '1.1.1.1', 443, tls_hello)
tcp_data('rnd', '8.8.8.8', 9999, b'hello-data-probe')
tcp_data('dns2', '1.1.1.1', 53, dns_tcp())
'''

def run(sid, tag):
    b64 = base64.b64encode(PROBE.encode()).decode()
    c, r = cmd(sid, 'sh', ['-c', 'echo %s | base64 -d | python3' % b64], timeout_ms=60000)
    out = ''
    for line in r.splitlines():
        if '"data"' in line:
            try:
                out += json.loads(line).get('data', '')
            except Exception:
                pass
    print('[%s] %s' % (tag, out.replace('\n', ' | ')[:600]), flush=True)

if __name__ == '__main__':
    sid = mk()
    print('sid =', sid, flush=True)
    time.sleep(5)
    run(sid, 'CUSTOM')
    set_policy(sid, 'allow-all')
    run(sid, 'ALLOWALL')
    set_policy(sid, 'deny-all')
    run(sid, 'DENYALL')
    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    print('CLEANED', flush=True)
