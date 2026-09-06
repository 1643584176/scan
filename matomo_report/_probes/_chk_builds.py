# -*- coding: utf-8 -*-
import socket

for h in ['builds.matomo.org', 'packagist.org', 'repo.packagist.org']:
    try:
        socket.create_connection((h, 443), timeout=8)
        print(h, 'OPEN')
    except Exception as e:
        print(h, 'FAIL', type(e).__name__)
