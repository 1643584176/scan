# -*- coding: utf-8 -*-
"""neon_auth 用户身份判定:user/account 的 email/provider(只查身份字段,不拉 token)"""
import psycopg

URI = 'postgresql://neondb_owner:npg_cI5ynlaAqjU2@ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build/neondb'
conn = psycopg.connect(URI, connect_timeout=20)
conn.autocommit = True
cur = conn.cursor()

def q(sql, fetch=True):
    try:
        cur.execute(sql)
        return cur.fetchall() if fetch else 'OK'
    except Exception as e:
        return 'ERR: %s' % str(e)[:400]

print('=== users ===')
print(q('SELECT id, email, role, "createdAt" FROM neon_auth."user"'))
print('\n=== accounts(身份列) ===')
print(q('SELECT "userId", "providerId", "accountId", scope FROM neon_auth.account'))
print('\n=== sessions(身份列,不含 token) ===')
print(q('SELECT id, "userId", "expiresAt", "ipAddress", "userAgent", "activeOrganizationId" FROM neon_auth.session'))
print('\n=== project_config ===')
print(q('SELECT name, endpoint_id, "trusted_origins", "webhook_config" FROM neon_auth.project_config'))

conn.close()
