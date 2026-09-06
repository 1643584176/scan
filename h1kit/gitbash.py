# -*- coding: utf-8 -*-
"""
gitbash.py - Git Bash on Windows pitfalls & workarounds.

Known traps (all observed repeatedly in this workspace):
  1. DOUBLE-QUOTES ARE STRIPPED by the bash layer for inline python -c "..."
     -> never use inline `python -c "code"`; write a script file and run
        `python < script.py` (stdin) instead.
  2. BACKTICKS in grep patterns are executed as command substitution
     (`order_by` inside a pattern -> "command not found").
  3. MSYS paths (/tmp/..., /c/...) are invisible to Windows-native python.
     Convert with winpath() before opening files.
  4. `cd /tmp && cmd` mixes msys cwd with windows cwd; keep scripts run
     from the workspace root and use absolute Windows paths in python.

Usage from a python script (F:\scan is cwd):
    from h1kit import gitbash
    print(gitbash.is_gitbash())
"""
import os
import re
import sys


def is_gitbash():
    """Detect running under Git Bash (or MSYS2) on Windows."""
    if os.name != 'nt':
        return False
    shell = os.environ.get('SHELL', '')
    if 'bash' in shell.lower() and ('MSYSTEM' in os.environ or 'Git' in shell):
        return True
    # qoder/terminal may not export SHELL; fall back to sh.exe in PATH
    if os.environ.get('MSYSTEM'):
        return True
    return False


def winpath(p):
    """
    Convert an MSYS-style path to a Windows path python can open.
      /tmp/foo          -> %TEMP%/foo          (git-bash /tmp maps to user temp)
      /c/Users/x         -> C:/Users/x
      /f/scan            -> F:/scan
    Non-msys paths are returned unchanged.
    """
    if not p:
        return p
    p2 = p.replace('\\', '/')
    if re.match(r'^[A-Za-z]:/', p2):
        return p2
    m = re.match(r'^/([a-zA-Z])/(.*)$', p2)
    if m:
        return '%s:/%s' % (m.group(1).upper(), m.group(2))
    m = re.match(r'^/tmp(?:/|$)(.*)$', p2)
    if m:
        tmp = os.environ.get('TEMP') or os.environ.get('TMP') or r'C:/Users/lbb/AppData/Local/Temp'
        rest = m.group(1)
        return (tmp + '/' + rest) if rest else tmp
    return p


def py_run_cmd(script_path, *args):
    """
    Return the recommended command line to execute a python script under
    git bash without quote-stripping issues: `python < script.py [args...]`.
    """
    parts = ['python', '<', script_path]
    parts.extend(args)
    return ' '.join(parts)


def pygrep(pattern, root, include=None, exclude_dirs=('.venv', '.git', '__pycache__',
                                                      'node_modules', '.idea'),
           max_hits=100, flags=0):
    """
    Regex grep implemented in python - immune to shell quote/backtick issues.

    Args:
        pattern:     python regex string (raw string recommended)
        root:        directory or single file to search
        include:     optional compiled regex; only paths matching it are scanned
        exclude_dirs: directory names skipped during walk
        max_hits:    stop after this many hits
        flags:       re flags (e.g. re.IGNORECASE)
    Returns:
        list of (filepath, lineno, line_text)
    """
    rx = re.compile(pattern, flags)
    hits = []
    files = []
    if os.path.isfile(root):
        files = [root]
    else:
        for dp, dns, fns in os.walk(root):
            dns[:] = [d for d in dns if d not in exclude_dirs]
            for fn in fns:
                files.append(os.path.join(dp, fn))
    for fp in files:
        if include and not include.search(fp):
            continue
        try:
            with open(fp, 'r', encoding='utf-8', errors='replace') as f:
                for ln, line in enumerate(f, 1):
                    if rx.search(line):
                        hits.append((fp, ln, line.rstrip('\n')[:300]))
                        if len(hits) >= max_hits:
                            return hits
        except OSError:
            continue
    return hits


def shell_memo():
    """Print the recurring git-bash traps as a reminder."""
    return (
        'Git Bash traps:\n'
        '  1. double quotes stripped -> never inline `python -c "..."`;\n'
        '     write a .py file and run: python < script.py\n'
        '  2. backticks in shell grep execute -> use h1kit.gitbash.pygrep()\n'
        '  3. /tmp paths are msys-virtual -> use h1kit.gitbash.winpath()\n'
        '  4. keep cwd at workspace root; use absolute Windows paths in python'
    )
