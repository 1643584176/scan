# -*- coding: utf-8 -*-
"""
h1kit - reusable toolkit for the recurring parts of H1 bug-bounty work.

Modules:
    gitbash   - git-bash pitfalls: quote stripping, msys paths, pygrep
    h1data    - program discovery & scope lookup (bounty-targets-data dump)
    net       - host reachability, proxy discovery, low-volume HTTP
    scaffold  - per-target report dir + rules-baseline doc skeleton

Typical flow:
    1. net.check_hosts(...) / net.probe_proxies()   when network state is unknown
    2. h1data.update_dump(); h1data.find_programs(...)   pick a target
    3. scaffold.make_report_dir(name) + make_baseline_md(handle, researcher)
    4. user pastes live policy -> test inside rules only
"""
from h1kit import gitbash, h1data, net, scaffold

__version__ = '1.0.0'
__all__ = ['gitbash', 'h1data', 'net', 'scaffold']
