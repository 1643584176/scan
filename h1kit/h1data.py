# -*- coding: utf-8 -*-
"""
h1data.py - HackerOne program data from arkadiyt/bounty-targets-data.

Provides offline program discovery + scope lookup:
  - find_programs(): keyword search over bounty-eligible open programs
  - program_info()/scope_assets(): per-handle in/out-of-scope assets

The dump only covers the repo's tracked programs (a subset of HackerOne,
e.g. ~450 managed/public entries) - use it for discovery, then confirm a
candidate's full policy with the researcher-provided page text (H1 policy
pages are a JS SPA and cannot be fetched anonymously - verified repeatedly).

Usage:
    from h1kit import h1data
    h1data.update_dump()
    rows = h1data.find_programs(keywords=['search', 'api'], exclude=['figma'])
    info = h1data.program_info('mongodb')
"""
import json
import os
import re
import sys
import time
import urllib.request

_DEFAULT_URL = ('https://raw.githubusercontent.com/arkadiyt/bounty-targets-data/'
                'main/data/hackerone_data.json')
_PKG_DIR = os.path.dirname(os.path.abspath(__file__))
DUMP_PATH = os.path.join(_PKG_DIR, 'cache', 'h1_data.json')


# ---------------------------------------------------------------- dump I/O
def update_dump(url=_DEFAULT_URL, force=False, quiet=False):
    """Download the latest hackerone_data.json into h1kit/cache."""
    if os.path.exists(DUMP_PATH) and not force:
        age = time.time() - os.path.getmtime(DUMP_PATH)
        if age < 86400 * 1 and not quiet:
            print('dump is fresh (%dd old): %s' % (age // 86400, DUMP_PATH))
            return DUMP_PATH
    if not quiet:
        print('downloading %s ...' % url)
    req = urllib.request.Request(url, headers={'User-Agent': 'h1kit/1.0'})
    with urllib.request.urlopen(req, timeout=120) as r:
        raw = r.read()
    os.makedirs(os.path.dirname(DUMP_PATH), exist_ok=True)
    with open(DUMP_PATH, 'wb') as f:
        f.write(raw)
    if not quiet:
        print('saved %d bytes -> %s' % (len(raw), DUMP_PATH))
    return DUMP_PATH


def load_dump(path=DUMP_PATH):
    """Load dump; returns list of program dicts."""
    if not os.path.exists(path):
        update_dump()
    with open(path, encoding='utf-8') as f:
        d = json.load(f)
    progs = d['hackerone'] if isinstance(d, dict) else d
    return progs


def _target_lists(p):
    """Normalize a program's targets dict {in_scope:[...], out_of_scope:[...]}."""
    t = p.get('targets') or {}
    if isinstance(t, dict):
        return t.get('in_scope') or [], t.get('out_of_scope') or []
    if isinstance(t, list):
        # some dumps store flat lists with eligible flags
        ins = [x for x in t if isinstance(x, dict) and x.get('eligible_for_submission')]
        return ins, []
    return [], []


# ---------------------------------------------------------------- discovery
def find_programs(keywords=(), exclude=(), bounty_only=True, state='open',
                  asset_types=('URL', 'DOMAIN'), max_rows=60, quiet=False,
                  min_efficiency=None, sort_by=None):
    """
    Search programs by keywords matched against name/url/asset identifiers.

    Args:
        keywords: list of regex fragments (OR-matched)
        exclude:  list of regex fragments excluded from name+url
        bounty_only: only programs offering bounties
        state:    submission_state filter ('open' | None for any)
        asset_types: asset types shown in the preview list
        max_rows: max rows returned
        min_efficiency: only programs with response_efficiency_percentage >= N
        sort_by:  'efficiency' (desc) | 'first_response' (asc, hours) |
                  'resolved' (asc, hours) | None (alphabetical)
    Returns:
        list of dicts: name, handle, url, n_targets, offers_bounties, assets,
        resp_eff, first_resp_h, resolved_h
    """
    kw_rx = re.compile('|'.join(keywords), re.I) if keywords else None
    ex_rx = re.compile('|'.join(exclude), re.I) if exclude else None
    rows = []
    for p in load_dump():
        name = p.get('name') or ''
        url = p.get('url') or ''
        handle = (url or '').rstrip('/').split('/')[-1]
        if bounty_only and not p.get('offers_bounties'):
            continue
        if state and (p.get('submission_state') or '') != state:
            continue
        if ex_rx and ex_rx.search(name + ' ' + url):
            continue
        eff = p.get('response_efficiency_percentage')
        if min_efficiency is not None and (eff or 0) < min_efficiency:
            continue
        ins, _ = _target_lists(p)
        blob = name + ' ' + url + ' ' + ' '.join(
            (t.get('asset_identifier') or '') for t in ins)
        if kw_rx and not kw_rx.search(blob):
            continue
        assets = [t.get('asset_identifier') for t in ins
                  if t.get('asset_type') in asset_types][:8]
        rows.append({'name': name, 'handle': handle, 'url': url,
                     'n_targets': len(ins), 'offers_bounties': p.get('offers_bounties'),
                     'assets': assets,
                     'resp_eff': eff,
                     'first_resp_h': p.get('average_time_to_first_program_response'),
                     'resolved_h': p.get('average_time_to_report_resolved')})
        if len(rows) >= max_rows * 3:
            break
    if sort_by == 'efficiency':
        rows.sort(key=lambda r: r['resp_eff'] or -1, reverse=True)
    elif sort_by == 'first_response':
        rows.sort(key=lambda r: r['first_resp_h'] if r['first_resp_h'] is not None else 1e9)
    elif sort_by == 'resolved':
        rows.sort(key=lambda r: r['resolved_h'] if r['resolved_h'] is not None else 1e9)
    else:
        rows.sort(key=lambda r: r['name'].lower())
    rows = rows[:max_rows]
    if not quiet:
        for r in rows:
            print('%-30s | %-38s | eff=%-3s | 1st=%-4s h | res=%-5s h | tg=%-3d | %s'
                  % (r['name'][:29], r['handle'][:37],
                     r['resp_eff'] if r['resp_eff'] is not None else '-',
                     r['first_resp_h'] if r['first_resp_h'] is not None else '-',
                     r['resolved_h'] if r['resolved_h'] is not None else '-',
                     r['n_targets'], ' '.join(r['assets'])[:100]))
        print('TOTAL: %d' % len(rows))
    return rows


# ---------------------------------------------------------------- per-handle
def program_info(handle, dump=None):
    """
    Return full info for one program handle (e.g. 'mongodb') or None.
    Dict keys: name, url, handle, offers_bounties, submission_state,
               in_scope(list), out_of_scope(list), updated.
    """
    for p in (dump if dump is not None else load_dump()):
        url = p.get('url') or ''
        if url.rstrip('/').endswith('/' + handle):
            ins, outs = _target_lists(p)
            return {'name': p.get('name'), 'url': url, 'handle': handle,
                    'offers_bounties': p.get('offers_bounties'),
                    'submission_state': p.get('submission_state'),
                    'in_scope': ins, 'out_of_scope': outs,
                    'updated': p.get('last_updated')}
    return None


def scope_assets(handle):
    """Shortcut: printable in/out-of-scope asset lines for a handle."""
    info = program_info(handle)
    if not info:
        return 'program %s not found in dump' % handle
    lines = ['== %s (%s) ==' % (info['name'], info['url']),
             'offers_bounties=%s submission_state=%s'
             % (info['offers_bounties'], info['submission_state'])]
    lines.append('-- in_scope (%d) --' % len(info['in_scope']))
    for t in info['in_scope']:
        lines.append('  %-14s %-6s eligible_bounty=%-5s %s'
                     % (t.get('asset_identifier', '')[:60],
                        t.get('asset_type', ''),
                        t.get('eligible_for_bounty'),
                        (t.get('instruction') or '')[:80]))
    lines.append('-- out_of_scope (%d) --' % len(info['out_of_scope']))
    for t in info['out_of_scope'][:20]:
        lines.append('  %-14s %-6s %s'
                     % (t.get('asset_identifier', '')[:60],
                        t.get('asset_type', ''),
                        (t.get('instruction') or '')[:80]))
    return '\n'.join(lines)
