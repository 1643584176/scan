# -*- coding: utf-8 -*-
"""清理 t4 测试创建的 5 个文件(移到回收站)"""
import json, sys, http.client, ssl, gzip, brotli
sys.path.insert(0, 'D:/scan/figma_report')
from _figma_creds import COOKIE_B

HOST = 'www.figma.com'
ORIGIN = 'https://www.figma.com'

KEYS = ['jOhdm0BST4GKpAJbOD3i03', 'egVuIEW4DcgHYFDi1cPBAZ', 'MyjSdK6yRgCZHBJ4Xf2laZ',
        'zAVWrZj2wUqCIz83pAzNpl', 'VSFoJXCbv9RblKaXjZNyfp']

ctx = ssl.create_default_context()
conn = http.client.HTTPSConnection(HOST, context=ctx, timeout=20)
body = json.dumps({'folder_items': [{'file': {'key': k}} for k in KEYS]})
hdrs = {'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'br, gzip',
        'Origin': ORIGIN, 'Referer': ORIGIN + '/', 'Cookie': COOKIE_B,
        'Content-Type': 'application/json', 'Content-Length': str(len(body))}
conn.request('PUT', '/api/folder_items/trash_bulk', body=body, headers=hdrs)
resp = conn.getresponse()
raw = resp.read()
enc = resp.getheader('Content-Encoding')
if enc == 'br':
    raw = brotli.decompress(raw)
conn.close()
print(resp.status, raw.decode('utf-8', 'ignore')[:400])
