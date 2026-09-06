# -*- coding: utf-8 -*-
"""
scaffold.py - project scaffold + rules-baseline doc generation.

Creates the per-target working layout used across all projects:
    <workspace>/<name>_report/
        <Name>-H1-rules-baseline.md   (english, from dump scope + placeholders)
        _js/        (downloaded frontend bundles)
        _probes/    (probe scripts, one hypothesis per script)

Full policy text cannot be fetched automatically (H1 policy pages are a JS
SPA - verified repeatedly). Workflow: run make_baseline_md() to scaffold,
then paste the researcher-visible policy into the doc (or ask the user to
provide it) and fill the checklist.

Usage:
    from h1kit import scaffold
    d = scaffold.make_report_dir('box')
    p = scaffold.make_baseline_md('mongodb', researcher='xxbo')
"""
import os
import datetime

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def make_report_dir(name, base=_ROOT):
    """
    Create <base>/<name>_report/{_js,_probes}. Returns the report dir path.
    Safe to call multiple times.
    """
    d = os.path.join(base, name.rstrip('/').replace('/', '_') + '_report')
    for sub in ('', '_js', '_probes'):
        os.makedirs(os.path.join(d, sub), exist_ok=True)
    return d


def _fmt_assets(assets, with_bounty=True):
    lines = []
    for t in assets:
        if with_bounty:
            lines.append('| %s | %s | %s | %s |'
                         % ((t.get('asset_identifier') or '')[:60].replace('|', '/'),
                            t.get('asset_type') or '',
                            'Yes' if t.get('eligible_for_bounty') else 'No',
                            (t.get('instruction') or '')[:90].replace('|', '/')))
        else:
            lines.append('| %s | %s | %s |'
                         % ((t.get('asset_identifier') or '')[:60].replace('|', '/'),
                            t.get('asset_type') or '',
                            (t.get('instruction') or '')[:90].replace('|', '/')))
    return '\n'.join(lines)


def make_baseline_md(handle, researcher='', out_dir=None, dump=None):
    """
    Generate an english rules-baseline skeleton for a program handle using
    the local dump scope. Returns the written file path.

    NOTE: dump scope is a subset & may lag the live page; the researcher must
    paste the live policy into the doc before testing starts.
    """
    from h1kit import h1data
    info = h1data.program_info(handle, dump=dump)
    if not info:
        raise ValueError('program handle %r not found in dump' % handle)
    d = out_dir or make_report_dir(info['name'].lower().replace(' ', ''))
    name_cap = ''.join(w.capitalize() for w in (info['name'] or handle).split())
    path = os.path.join(d, '%s-H1-rules-baseline.md' % name_cap)
    today = datetime.date.today().isoformat()
    in_scope = _fmt_assets(info['in_scope'], with_bounty=True)
    out_scope = _fmt_assets(info['out_of_scope'], with_bounty=False)
    md = (
        '# %s - Rules Baseline\n\n'
        '> Program: %s | Dump date: %s | Researcher: %s\n'
        '> **Policy pages are user-provided: paste the live policy below '
        'before testing.**\n\n'
        '## 1. Policy (paste from HackerOne policy page)\n\n'
        '```\nTODO: paste full policy (rules, eligibility, testing '
        'instructions, rewards, exclusions)\n```\n\n'
        '## 2. In-Scope Assets (from bounty-targets dump, verify live)\n\n'
        '| Asset | Type | Bounty | Instruction |\n|---|---|---|---|\n%s\n\n'
        '## 3. Out-of-Scope (from dump; verify live)\n\n'
        '| Asset | Type | Instruction |\n|---|---|---|\n%s\n\n'
        '## 4. Hard Rules Checklist (fill from policy)\n\n'
        '- [ ] Account naming / test-account constraints\n'
        '- [ ] Allowed methods / rate limits / no-scanner rule\n'
        '- [ ] Test only own data; no third-party interaction\n'
        '- [ ] Known-findings / exclusions list reviewed\n'
        '- [ ] Report requirements (ids, timestamps, headers)\n'
        '- [ ] Rewards table + severity rationale\n\n'
        '## 5. Execution Discipline\n\n'
        '- One probe script = one hypothesis + baseline control + single-variable mutations\n'
        '- Log account/IP/timestamp per report requirement\n'
        '- Dedupe + impact-first writeup before any submission\n'
    ) % (name_cap, info['url'], today, researcher, in_scope, out_scope)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(md)
    return path
