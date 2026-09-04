// Netlify probe7: extension 二进制深挖 - lambda-events 上下文 + 路径常量
const fs = require('fs');

exports.handler = async () => {
  const out = {};
  const BIN = '/opt/extensions/netlify-observability-extension';
  try {
    const buf = fs.readFileSync(BIN);
    const s = buf.toString('latin1');
    // 1. lambda-events 上下文
    out.ctx = [];
    let idx = 0;
    while (out.ctx.length < 12) {
      const i = s.indexOf('lambda-events', idx);
      if (i < 0) break;
      out.ctx.push(s.slice(Math.max(0, i - 400), i + 400).replace(/[^\x20-\x7e]/g, '.'));
      idx = i + 1;
    }
    // 2. Go 字符串中的路径常量(引号包裹的 /xxx)
    const paths = [];
    const re = /"(\/[A-Za-z0-9_\-\.\{\}:]{2,90})"/g;
    let m;
    while ((m = re.exec(s)) && paths.length < 80) {
      if (!paths.includes(m[1])) paths.push(m[1]);
    }
    out.paths = paths;
    // 3. events/trace/ingest 相关路径(无引号也可能)
    const evs = [];
    const re2 = /([A-Za-z0-9_\-\.\/]{0,60}(?:event|trace|ingest|telemetry|span|metric|log|export)[A-Za-z0-9_\-\.\/]{0,60})/gi;
    while ((m = re2.exec(s)) && evs.length < 80) {
      const v = m[1];
      if (!evs.includes(v) && /[\/\.]/.test(v) && !/^[A-Za-z0-9_\-]{40,}$/.test(v)) evs.push(v);
    }
    out.eventRefs = evs;
    // 4. POST/PUT 相关行上下文(找 http method 使用的路径)
    const posts = [];
    const re3 = /(POST|PUT|PATCH|"GET")([^\x00-\x1f]{0,120})/g;
    while ((m = re3.exec(s)) && posts.length < 40) {
      const v = m[0].replace(/[^\x20-\x7e]/g, '.');
      if (!posts.includes(v)) posts.push(v);
    }
    out.postRefs = posts;
  } catch (e) {
    out.err = String(e);
  }
  return { statusCode: 200, body: JSON.stringify(out) };
};
