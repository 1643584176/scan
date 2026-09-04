# -*- coding: utf-8 -*-
"""读 member/invitation 行 id(本地),供 API 矩阵使用"""
import psycopg, json

URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'
conn = psycopg.connect(URI, connect_timeout=15)
cur = conn.cursor()
cur.execute('SELECT id, "organizationId", "userId", role FROM neon_auth.member ORDER BY "createdAt"')
print('members:')
for r in cur.fetchall():
    print(' ', r)
cur.execute('SELECT id, "organizationId", email, role, status FROM neon_auth.invitation ORDER BY "createdAt"')
print('invitations:')
for r in cur.fetchall():
    print(' ', r)
cur.execute('SELECT id, name, slug FROM neon_auth.organization ORDER BY "createdAt"')
print('orgs:')
for r in cur.fetchall():
    print(' ', r)
conn.close()
