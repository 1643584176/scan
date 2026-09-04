// Netlify probe9: 分块下载 /opt/extensions/netlify-observability-extension(参数 start/size,返回 base64)
const fs = require('fs');

exports.handler = async (event) => {
  const q = (event && event.queryStringParameters) || {};
  const start = parseInt(q.start || '0', 10);
  const size = parseInt(q.size || '300000', 10);
  const BIN = '/opt/extensions/netlify-observability-extension';
  try {
    const st = fs.statSync(BIN);
    const total = st.size;
    const fd = fs.openSync(BIN, 'r');
    const buf = Buffer.alloc(Math.min(size, total - start));
    fs.readSync(fd, buf, 0, buf.length, start);
    fs.closeSync(fd);
    return {
      statusCode: 200,
      body: JSON.stringify({ total, start, len: buf.length, b64: buf.toString('base64') }),
    };
  } catch (e) {
    return { statusCode: 500, body: JSON.stringify({ err: String(e) }) };
  }
};
