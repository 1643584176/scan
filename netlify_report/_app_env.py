# -*- coding: utf-8 -*-
"""追加 env API 结论 + 尝试清理 SITE_A cd 残留"""
txt = r'''

### env API(/api/v1/accounts/{acc}/env + /sites/{id}/env)—— 关闭(单账号变异无洞)
- 形态: GET /sites/{id}/env 或 GET /accounts/{acc}/env?site_id= (等价, URL account 参数被忽略纯装饰); POST /accounts/{acc}/env?site_id= body=[{key, values:[{context,value,context_parameter}]}] -> 201; DELETE /accounts/{acc}/env/{key}?site_id= -> 204; PATCH|PUT /accounts/{acc}/env/{key}?site_id=&context= -> 200 更新
- 校验: 一律 token<->site 强绑定; URL account 参数换谁的都行(忽略); 跨账号读写删改全 404; 匿名 401
- 免费 plan 墙: body 带 scopes -> 403 "Upgrade...to set specific scopes"; POST 无 site_id(共享 env)-> 403 "shared environment variables"
- GET 明文返回(owner), 含 updated_by 用户信息; context 过滤语义正确(branch 只回 branch)
- 校验矩阵: key 字母开头字母数字下划线 <=255; value <=5000 必须 string(null 存空串, 数字/对象/数组 422); context 白名单 production/all/deploy-preview/branch(+param); branch param 保留名(main)422; key 已存在需走更新接口
- 写入后瞬时 GET 401 现象(自动恢复, 非 bug)
- 结论: 多租户边界严密无越权; 剩余未测 = 角色级(guest/member 读 env 脱敏/写权限)需先建 team 协作关系
'''
with open(r'D:\scan\netlify_report\progress-2026-09-02.md', 'a', encoding='utf-8') as f:
    f.write(txt)

# 尝试清理 A 站 custom_domain 残留
import http.client, ssl, gzip, brotli, json, sys, time
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, SITE_A
ctx = ssl.create_default_context()
def req(method, path, body=None, timeout=20):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': 'application/json',
         'Authorization': 'Bearer ' + TOKEN_A}
    b = json.dumps(body).encode() if body is not None else None
    conn.request(method, path, body=b, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br': raw = brotli.decompress(raw)
    elif enc == 'gzip': raw = gzip.decompress(raw)
    st = r.status
    t2 = raw.decode('utf-8', 'ignore')
    conn.close()
    return st, t2

st, b = req('GET', '/api/v1/sites/' + SITE_A)
try:
    j = json.loads(b)
    print('A cd =', j.get('custom_domain'), 'name =', j.get('name'))
except Exception:
    print('GET fail', st, b[:100])
if json.loads(b).get('custom_domain') not in (None, ''):
    st, b = req('PATCH', '/api/v1/sites/' + SITE_A, {'custom_domain': None})
    print('PATCH cd=null ->', st, b[:100])
    if st == 200:
        st, b = req('PATCH', '/api/v1/sites/' + SITE_A, {'name': 'sec-test-rcf6lz'})
        print('restore name ->', st, b[:80])
print('cleanup done')
