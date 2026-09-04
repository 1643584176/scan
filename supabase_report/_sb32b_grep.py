# -*- coding: utf-8 -*-
"""全文搜索 spec 是否含 jit-access/ssl-enforcement 定义"""
import os

d = os.path.dirname(os.path.abspath(__file__))
t = open(os.path.join(d, '_sb16_openapi.json'), encoding='utf-8').read()
for k in ['jit-access', 'ssl-enforcement', 'JitAccess', 'SslEnforcement', 'login-role', 'jit_access', 'readReplica', 'read-replica']:
    print('%-20s idx=%s' % (k, t.find(k)))
