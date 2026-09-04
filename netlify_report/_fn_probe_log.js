'use strict';
// probe-log:记录收到的请求并返回 manifest 形态响应,验证 sdk-version 服务端解析/回显
const fs = require('fs');

exports.handler = async (event) => {
  const rec = JSON.stringify({
    when: Date.now(),
    url: event.rawUrl || (event.path || ''),
    method: event.httpMethod,
    headers: event.headers || {},
    body: (event.body || '').slice(0, 500),
  });
  try { fs.appendFileSync('/tmp/probe_log.txt', rec + '\n'); } catch (e) {}
  const q = event.queryStringParameters || {};
  if (q.mode === 'sleep') {
    const ms = Math.min(parseInt(q.ms || '3000', 10), 15000);
    await new Promise(r => setTimeout(r, ms));
    return { statusCode: 200, headers: { 'content-type': 'application/json' }, body: JSON.stringify({ slept: ms }) };
  }
  if (q.dump === '1') {
    let d = '';
    try { d = fs.readFileSync('/tmp/probe_log.txt', 'utf8'); } catch (e) { d = '(empty)'; }
    return { statusCode: 200, headers: { 'content-type': 'application/json' }, body: JSON.stringify({ dump: d }) };
  }
  if (q.mode === 'text') {
    return { statusCode: 200, headers: { 'content-type': 'text/plain' }, body: 'hello plain text' };
  }
  if (q.mode === 'manifest') {
    return {
      statusCode: 200, headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ name: 'demo-ext', sdkVersion: 'TESTMARKER_7f3a', isExtensionSite: true }),
    };
  }
  return {
    statusCode: 200, headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ isExtensionSite: true, sdkVersion: 'TESTMARKER_' + Buffer.from(rec).toString('base64').slice(0, 400) }),
  };
};
