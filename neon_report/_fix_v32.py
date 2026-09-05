# -*- coding: utf-8 -*-
import re
p = r"F:\scan\neon_report\_v32_console_surface.py"
s = open(p, encoding="utf-8").read()
# paths are stored as "GET /xxx" tuples; strip the "GET " prefix since api() takes method separately
s = re.sub(r'\("([a-z_ /]+)", "GET (/[^"]+)"\)', r'("\1", "\2")', s)
open(p, "w", encoding="utf-8").write(s)
print("fixed", len(re.findall(r'\("([a-z_ /]+)", "(/|projects)', s)), "tuples now method-less")
