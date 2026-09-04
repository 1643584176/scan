# -*- coding: utf-8 -*-
import zipfile, sys
z = zipfile.ZipFile(sys.argv[1])
for info in z.infolist():
    print(info.filename, '| compressed:', info.compress_size, '| original:', info.file_size, '| method:', info.compress_type)
# dump index.js 前 500 字节
data = z.read('index.js')
print('--- index.js head ---')
print(data[:600].decode('utf-8', 'replace'))
