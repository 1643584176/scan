import importlib.util, sys, traceback
spec = importlib.util.spec_from_file_location('pty2', r'F:\scan\_x_pty2.py')
m = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(m)
    print('IMPORT OK', m.NAME)
except SystemExit as e:
    print('SYSTEMEXIT', e)
    traceback.print_exc()
except BaseException as e:
    print('EXC', type(e).__name__, e)
    traceback.print_exc()
