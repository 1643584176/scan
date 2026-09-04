// Netlify probe8: 二进制中 NETLIFY_FUNCTIONS_TOKEN 引用上下文 + ingest 路径构造线索
const fs = require('fs');

exports.handler = async () => {
  const out = {};
  const BIN = '/opt/extensions/netlify-observability-extension';
  try {
    const buf = fs.readFileSync(BIN);
    const s = buf.toString('latin1');
    // 1. NETLIFY_FUNCTIONS_TOKEN / FUNCTIONS_TOKEN 上下文
    out.tokCtx = [];
    for (const kw of ['NETLIFY_FUNCTIONS_TOKEN', 'FUNCTIONS_TOKEN', 'NF_TOKEN', 'nfToken', 'functionsToken']) {
      let idx = 0;
      let cnt = 0;
      while (cnt < 6) {
        const i = s.indexOf(kw, idx);
        if (i < 0) break;
        out.tokCtx.push('[' + kw + '] ' + s.slice(Math.max(0, i - 250), i + 350).replace(/[^\x20-\x7e]/g, '.'));
        idx = i + 1;
        cnt++;
      }
    }
    // 2. 找 http header 名常量(extension 请求用哪些 header)
    const hdrs = [];
    const re = /"(x-[a-z0-9\-]+|authorization|content-type|accept|netlify-[a-z0-9\-]+|nf-[a-z0-9\-]+)"/gi;
    let m;
    while ((m = re.exec(s)) && hdrs.length < 40) {
      if (!hdrs.includes(m[1].toLowerCase())) hdrs.push(m[1].toLowerCase());
    }
    out.headers = hdrs;
    // 3. 路径片段常量(单个 "/xxx" 无引号包整个路径,找含 v1/v2/event/record 的短串)
    const frags = [];
    const re2 = /([A-Za-z0-9_\-]{2,40})\/(v[0-9]|event|record|batch|ingest|telemetry|trace|metric|log|report|dispatch)[A-Za-z0-9_\-/]{0,40}/gi;
    while ((m = re2.exec(s)) && frags.length < 60) {
      const v = m[0];
      if (!frags.includes(v) && v.length > 3 && v.length < 90) frags.push(v);
    }
    out.frags = frags;
    // 4. URL 构造:找 "%s" 格式串附近或 http client 目标
    const fmt = [];
    const re3 = /https?:\/\/%[A-Za-z0-9_\-\.%\/:]{0,80}/g;
    while ((m = re3.exec(s)) && fmt.length < 20) fmt.push(m[0]);
    out.urlFmt = fmt;
  } catch (e) {
    out.err = String(e);
  }
  return { statusCode: 200, body: JSON.stringify(out) };
};
