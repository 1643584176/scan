# -*- coding: utf-8 -*-
import sqlite3
import os
p = r'C:\Users\tndc2\AppData\Local\Google\Chrome\User Data\Default\Network\Cookies'
print('exists:', os.path.exists(p), os.path.getsize(p) if os.path.exists(p) else '-')
try:
    con = sqlite3.connect('file:%s?mode=ro' % p.replace('\\', '/'), uri=True)
    cur = con.cursor()
    cur.execute("SELECT host_key, name, length(value) FROM cookies WHERE host_key LIKE '%vercel%' OR name LIKE '%vercel%'")
    rows = cur.fetchall()
    print('rows:', len(rows))
    for r in rows:
        print(r)
    con.close()
except Exception as e:
    print('ERR', repr(e))
