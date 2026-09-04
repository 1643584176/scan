const { zipFunctions } = require('@netlify/zip-it-and-ship-it');
zipFunctions(
  'D:/scan/netlify_report/_zisi/fnsrc',
  'D:/scan/netlify_report/_zisi/out2',
  { basePath: 'D:/scan/netlify_report/_zisi/fnsrc', config: { nodeVersion: '22.x' } }
)
  .then((res) => {
    console.log(JSON.stringify(res.map((r) => ({ name: r.name, path: r.path, runtime: r.runtime, size: r.size })), null, 1));
    const fs = require('fs');
    const path = require('path');
    for (const r of res) {
      console.log('--- zip listing:', path.basename(r.path));
      const zip = fs.readFileSync(r.path);
      // 用 yauzl? 简单:unzip via powershell 不可;直接打印 zip 头信息不现实。改用 node 的 child? 这里跳过,后续用 python 列
    }
  })
  .catch((e) => { console.error('ERR', e.message); process.exit(1); });
