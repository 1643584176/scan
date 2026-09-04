const fs = require('fs');
const os = require('os');
exports.handler = async () => {
  const out = { env: [], hosts: '', resolv: '', ifaces: {}, fs: {}, aws: [] };
  out.env = Object.keys(process.env).map((k) => {
    const v = process.env[k] || '';
    return k + '=' + (v.length > 80 ? v.slice(0, 30) + '..len' + v.length : v);
  });
  try { out.hosts = fs.readFileSync('/etc/hosts', 'utf8'); } catch (e) { out.hosts = 'ERR ' + e; }
  try { out.resolv = fs.readFileSync('/etc/resolv.conf', 'utf8'); } catch (e) {}
  try {
    const ifs = os.networkInterfaces();
    const brief = {};
    for (const k of Object.keys(ifs)) brief[k] = (ifs[k] || []).map((i) => i.address + '/' + i.netmask + (i.internal ? '(lo)' : ''));
    out.ifaces = brief;
  } catch (e) { out.ifacesErr = String(e); }
  const rd = (p) => { try { return fs.readdirSync(p); } catch (e) { return 'ERR ' + String(e).slice(0, 60); } };
  out.fs.cwd = process.cwd();
  out.fs.home = os.homedir();
  out.fs.varTask = rd('/var/task');
  out.fs.opt = rd('/opt');
  out.fs.tmp = rd('/tmp').slice(0, 20);
  try { out.fs.proc1Cmd = fs.readFileSync('/proc/1/cmdline', 'utf8').replace(/\0/g, ' '); } catch (e) {}
  try { out.fs.mounts = fs.readFileSync('/proc/self/mountinfo', 'utf8').split('\n').slice(0, 40); } catch (e) {}
  try { out.fs.procEnviron = (fs.readFileSync('/proc/self/environ', 'utf8') || '').replace(/\0/g, '|').slice(0, 600); } catch (e) {}
  for (const u of [
    'https://sts.us-east-2.amazonaws.com/',
    'https://lambda.us-east-2.amazonaws.com/',
    'https://s3.us-east-2.amazonaws.com/',
    'http://169.254.169.254/latest/meta-data/iam/security-credentials/',
    'http://169.254.170.2/v2/credentials',
  ]) {
    try {
      const ctl = new AbortController();
      const t = setTimeout(() => ctl.abort(), 3000);
      const r = await fetch(u, { signal: ctl.signal });
      clearTimeout(t);
      out.aws.push(u + ' => ' + r.status + ' len=' + (await r.text()).length);
    } catch (e) { out.aws.push(u + ' => ERR ' + String(e).slice(0, 80)); }
  }
  return { statusCode: 200, body: JSON.stringify(out) };
};
