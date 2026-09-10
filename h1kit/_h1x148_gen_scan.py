# -*- coding: utf-8 -*-
"""从 handles 列表生成凭证存在性扫描浏览器块"""
import json

hs = json.load(open('D:/scan/h1kit/_h1x148_handles.json', encoding='utf-8'))
chunks = [hs[i:i + 3] for i in range(0, len(hs), 3)]

L = []
L.append('(async () => {')
L.append('  const sleep = ms => new Promise(r => setTimeout(r, ms));')
L.append('  const csrf = document.querySelector(\'meta[name="csrf-token"]\').content;')
L.append('  const hits = [];')
L.append('  const q = async (handle) => {')
L.append('    const r = await fetch("/graphql", {')
L.append("      method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf },")
L.append('      body: JSON.stringify({ query: `{ team(handle: "${handle}") { structured_scopes { edges { node { id asset_identifier credentials_available_count credentials_claimed_count } } } } }` })')
L.append('    });')
L.append('    const j = await r.json();')
L.append('    const sc = j?.data?.team?.structured_scopes?.edges || [];')
L.append('    for (const e of sc) {')
L.append('      const n = e.node;')
L.append('      if (n.credentials_available_count > 0 || n.credentials_claimed_count > 0)')
L.append('        hits.push(handle + " | " + n.asset_identifier + " | avail=" + n.credentials_available_count + " claimed=" + n.credentials_claimed_count);')
L.append('    }')
L.append('  };')
for i, c in enumerate(chunks):
    parts = []
    for h in c:
        parts.append('await q(%r)' % h)
    L.append('  try { ' + '; '.join(parts) + '; } catch (e) {}')
    L.append('  await sleep(160);')
L.append('  const ta = document.createElement("textarea");')
L.append("  ta.style.cssText = 'position:fixed;top:0;left:0;width:97%;height:92%;z-index:999999;font:10px monospace;white-space:pre;';")
L.append("  ta.value = 'HITS (' + hits.length + '):\\n' + hits.join('\\n') + '\\n\\n(empty = no scope has credentials)';")
L.append('  document.body.appendChild(ta); ta.focus(); ta.select();')
L.append('})();')

block = '\n'.join(L)
open('D:/scan/h1kit/_h1x148_scan_block.txt', 'w', encoding='utf-8').write(block)
print('block lines:', len(L), '| chunk count:', len(chunks))
print(block[:600])
