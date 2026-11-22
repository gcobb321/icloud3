'''Every module imports (Home Assistant replaced by stubs, see import_all.py)'''
import subprocess
import sys
from pathlib import Path


def check(code, r):
    for rel, err in code.syntax_errors:
        r.error(f"{rel}: syntax error: {err}")
    script = Path(__file__).with_name('import_all.py')
    out = subprocess.run([sys.executable, '-B', str(script), str(code.root)],
                         capture_output=True, text=True, timeout=300)
    lines = (out.stdout + out.stderr).strip().splitlines()
    for line in lines:
        if line.startswith('FAIL '):
            r.error(line[5:])
    if out.returncode and not any(l.startswith('FAIL ') for l in lines):
        r.error(f"import_all.py failed: {' / '.join(lines[-5:])}")
    elif lines:
        r.info(lines[-1])
