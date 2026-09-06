# -*- coding: utf-8 -*-
"""Final verify: config flag + login via API."""
import re
import urllib.parse

# 1) config
raw = open(r'F:\scan\matomo_report\_src\matomo-release\matomo\config\config.ini.php', 'rb').read()
txt = raw.decode('utf-8', 'replace')
print('has installation_in_progress:', 'installation_in_progress' in txt)
print('has salt:', bool(re.search(r'salt\s*=', txt)))
print('has trusted_hosts:', 'trusted_hosts' in txt)
print('has database username:', bool(re.search(r'username\s*=\s*"matomo"', txt)))
print('cfg bytes:', len(raw))
