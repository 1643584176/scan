# -*- coding: utf-8 -*-
"""报告有效性复测: 文件公开状态 + versions + make_versions + code_snapshot + published_package
目的: 验证已提交的两份报告在当前状态下是否仍然成立(排除公开文件/污染cookie假象)
"""
import io, json, sys, urllib.error, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
MAKE_FILE = "5zb5YkoxMa09KpqOyuLcHD"     # A 的 Make 文件(报告1 声称私有)
PUB_LIB = "bv2nMIdFf4u3dESGail4sm"        # A 的公开库(报告2 目标)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36"
A_UID = "1666382703778278399"
B_UID = "1667396392129259941"


def load(p):
    return io.open(p, encoding='utf-8').read().strip().replace('\n', '; ')


AC = load('ws_cookie_A_new.txt')
BC = load('ws_cookie_B_new.txt')

# 构造纯净 B cookie: authn/embed 只留 B token
def make_pure_b(raw):
    pairs = []
    for pair in raw.split('; '):
        if '__Host-figma.authn=' in pair or '__Host-figma.embed=' in pair:
            name, val = pair.split('=', 1)
            val = urllib.parse.unquote(val)
            d = json.loads(val)
            d = {k: v for k, v in d.items() if k == B_UID}
            pairs.append(name + '=' + urllib.parse.quote(json.dumps(d)))
        else:
            pairs.append(pair)
    return '; '.join(pairs)


PBC = make_pure_b(BC)
print("PURE B authn:", [p[:60] for p in PBC.split('; ') if 'authn' in p])


def call(label, path, cookie=None, method="GET", body=None, query=None, headers_extra=None):
    url = BASE + path
    if query:
        url += '?' + urllib.parse.urlencode(query)
    h = {'User-Agent': UA, 'Accept': 'application/json'}
    if cookie:
        h['Cookie'] = cookie
    if headers_extra:
        h.update(headers_extra)
    data = None
    if body is not None:
        h['Content-Type'] = 'application/json'
        data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read().decode(errors='replace')
            print(f'[{label}] HTTP {r.status} {raw[:450]}')
            return r.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors='replace')
        print(f'[{label}] HTTP {e.code} {raw[:300]}')
        return e.code, raw
    except Exception as e:
        print(f'[{label}] ERR {type(e).__name__} {str(e)[:120]}')
        return None, str(e)


print("========== 1. Make 文件公开状态 ==========")
call('A metadata', f'/api/files/{MAKE_FILE}', cookie=AC)
call('ANON metadata', f'/api/files/{MAKE_FILE}')
call('PUREB metadata', f'/api/files/{MAKE_FILE}', cookie=PBC)

print("\n========== 2. versions API ==========")
st, raw = call('A versions', f'/api/versions/{MAKE_FILE}?page_size=10', cookie=AC)
vid = None
try:
    vs = json.loads(raw).get('meta', {}).get('versions', [])
    if vs:
        vid = vs[0].get('id')
        print('  first version id:', vid)
except Exception as e:
    print('  parse err', e)
call('ANON versions', f'/api/versions/{MAKE_FILE}?page_size=10')
call('PUREB versions', f'/api/versions/{MAKE_FILE}?page_size=10', cookie=PBC)

print("\n========== 3. make_versions REST (需要 thread id, 用 A owner 拿) ==========")
st, raw = call('A threads', f'/api/ai_chat/threads?owner_id={MAKE_FILE}&owner_type=file', cookie=AC)
tid = None
try:
    threads = json.loads(raw).get('meta', {}).get('threads', [])
    for t in threads:
        if t.get('id'):
            tid = t['id']
            print('  first thread id:', tid)
            break
except Exception as e:
    print('  parse err', e)

if tid:
    call('A make_versions', f'/api/ai_chat/{MAKE_FILE}/make_versions/{tid}?page_size=10', cookie=AC)
    call('ANON make_versions', f'/api/ai_chat/{MAKE_FILE}/make_versions/{tid}?page_size=10')
    call('PUREB make_versions', f'/api/ai_chat/{MAKE_FILE}/make_versions/{tid}?page_size=10', cookie=PBC)

print("\n========== 4. published_package (报告2) ==========")
call('PUREB create pkg', f'/api/files/{PUB_LIB}/published_package', cookie=PBC, method='POST',
     body={"package_identifier": "verify-report2", "package_type": "npm"})
