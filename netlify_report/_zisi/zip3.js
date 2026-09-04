// 打包 probe-log 函数
const { zipFunctions } = require('D:/scan/netlify_report/_zisi/node_modules/@netlify/zip-it-and-ship-it');
zipFunctions('D:/scan/netlify_report/_zisi/fnsrc', 'D:/scan/netlify_report/_zisi/out3',
  { basePath: 'D:/scan/netlify_report/_zisi/fnsrc', config: { nodeVersion: '22.x' } })
  .then(r => console.log('zip done:', r.map(x => x.path)))
  .catch(e => console.error('ERR', e.message));
