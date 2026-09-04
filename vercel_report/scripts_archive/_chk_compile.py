import py_compile, sys
try:
    py_compile.compile(r'F:\scan\_x_pty2.py', doraise=True)
    print('COMPILE OK')
except Exception as e:
    print('COMPILE FAIL:', repr(e))
