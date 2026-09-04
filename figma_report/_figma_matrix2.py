# -*- coding: utf-8 -*-
"""Figma 对照测试矩阵 v2:带完整认证头(tsid + x-csrf-bypass)
A. 基线复验
B. AI 对话线程(owner=A 文件)——创建线程看是否泄露 A 的数据
C. PUT /api/files/A 最小修改(改后立即恢复)
D. PUT /api/files/B 对照
E. 其他写端点(variables/publish_state 等)
"""
import sys, json, time, requests, urllib3
sys.path.insert(0, 'D:/scan/figma_report')
from _figma_creds import COOKIE_B, UID_A, UID_B, FILE_A, FILE_B, TEAM_B, PLAN_B
urllib3.disable_warnings()

BASE = 'https://www.figma.com'
TSID = 'mk' + str(int(time.time() * 1000))[-14:]
print('TSID:', TSID)

S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}
S.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                  'Cookie': COOKIE_B,
                  'tsid': TSID,
                  'x-csrf-bypass': 'yes',
                  'x-figma-client-version': '24850ed350d86c5466f8b775996885ec28db9f19',
                  'x-figma-user-id': UID_B,
                  'origin': 'https://www.figma.com',
                  'content-type': 'application/json'})

def req(method, path, label='', **kw):
    kw.setdefault('timeout', 15)
    r = S.request(method, BASE + path, verify=False, **kw)
    print('[%s] %s %s -> %d' % (method, label or path[:70], '', r.status_code))
    print('   %s' % r.text[:350].replace('\n', ' '))
    return r

print('=== A. 基线(带完整头) ===')
req('GET', '/api/session/state', 'session/state')

print('\n=== B. AI 对话线程(owner=A 文件) ===')
r = req('POST', '/api/ai_chat/threads', 'threads(owner=A)',
        json={'owner_id': FILE_A, 'owner_type': 'file', 'thread_type': 'assistant',
              'plan_id': PLAN_B, 'privacy_mode': 'file'})

print('\n=== C. PUT /api/files/A 最小修改(只改 thumbnail 之类无害字段,随后恢复) ===')
# 先读当前 meta
r0 = req('GET', '/api/file_metadata/%s' % FILE_A, 'file_metadata(A)')
name0 = None
try:
    name0 = r0.json()['meta'].get('name')
except Exception:
    pass
# 用原 name 提交(幂等,无实际修改)
r = req('PUT', '/api/files/%s' % FILE_A, 'PUT files(A) name=原值',
        json={'name': name0 or '第一个', 'is_auto_save': True, 'file_type': 'design'})
print('   (提交 name=原值,理论上无变化)')

print('\n=== D. PUT /api/files/B 对照 ===')
r = req('PUT', '/api/files/%s' % FILE_B, 'PUT files(B)',
        json={'name': 'Untitled', 'is_auto_save': True, 'file_type': 'design'})

print('\n=== E. 其他写端点 ===')
req('POST', '/api/variables/publish_state', 'variables/publish_state(空)',
    params={'keysAndLibrary': 'test'}, json={})
req('POST', '/api/files/create', 'files/create',
    json={'editor_type': 'design', 'team_id': TEAM_B, 'from': 'test', 'triggerElement': 'test'})
