# -*- coding: utf-8 -*-
"""从 Chrome/Edge 提取 vercel.com 登录 cookie (DPAPI 解密)"""
import os, sqlite3, shutil, json
import ctypes
from ctypes import wintypes

CHROME = os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data\Default\Network\Cookies')
EDGE = os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Network\Cookies')


def dpapi_decrypt(blob):
    class DATA_BLOB(ctypes.Structure):
        _fields_ = [('cbData', wintypes.DWORD), ('pbData', ctypes.POINTER(ctypes.c_char))]

    buf = ctypes.create_string_buffer(blob, len(blob))
    b_in = DATA_BLOB(len(blob), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))
    b_out = DATA_BLOB()
    if not ctypes.windll.crypt32.CryptUnprotectData(
            ctypes.byref(b_in), None, None, None, None, 0, ctypes.byref(b_out)):
        return None
    out = ctypes.string_at(b_out.pbData, b_out.cbData)
    ctypes.windll.kernel32.LocalFree(b_out.pbData)
    return out


def try_decrypt(value):
    if not value:
        return None
    # v10: DPAPI blob
    if value.startswith(b'v10'):
        return dpapi_decrypt(value[3:])
    if value.startswith(b'v20'):
        # app-bound encryption, 需要 LocalState key, 复杂; 标记出来
        return b'<v20-appbound>'
    return value


def extract(path, label):
    if not os.path.exists(path):
        print('[%s] not found' % label)
        return
    tmp = path + '.tmpcopy'
    try:
        shutil.copy2(path, tmp)
        con = sqlite3.connect(tmp)
        cur = con.cursor()
        cur.execute("SELECT host_key, name, path, expires_utc, value FROM cookies WHERE host_key LIKE '%vercel%' OR name LIKE '%vercel%'")
        rows = cur.fetchall()
        print('[%s] vercel cookies: %d' % (label, len(rows)))
        for host, name, cpath, exp, value in rows:
            dec = try_decrypt(value)
            if dec is None:
                print('  %-30s %-25s -> DECRYPT_FAIL' % (host, name))
            else:
                print('  %-30s %-25s -> %s' % (host, name, dec[:200]))
        con.close()
    except Exception as e:
        print('[%s] ERR %s' % (label, e))
    finally:
        try:
            os.remove(tmp)
        except Exception:
            pass


extract(CHROME, 'chrome')
extract(EDGE, 'edge')
