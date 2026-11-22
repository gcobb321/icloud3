#!/usr/bin/env python3
'''
Quick static checks of the iCloud3 code and texts. No Home Assistant install needed.

    python tests/check_configure.py [DIR] [-v]

DIR contains custom_components/icloud3 (default: this repository). -v also lists the
INFO lines (allowed findings, values the checks can't follow).
Exit code 1 if there is an ERROR. WARN lines are listed but don't fail the check.
'''
import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from checks.common import Code, Results
from checks import imports, placeholders, references, text_keys, translations

CHECKS = [
    ('strings.json and translations/*.json', translations.check),
    ('every module imports', imports.check),
    ('names the code uses exist', references.check),
    ('text keys the code uses exist', text_keys.missing),
    ('screen texts: placeholders, step texts, error keys', placeholders.check),
    ('text keys no code refers to', text_keys.unused),
]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    verbose = '-v' in sys.argv
    root = Path(args[0]) if args else Path(__file__).resolve().parents[1]
    code = Code(root)
    totals = {'ERROR': 0, 'WARN': 0}
    for title, check in CHECKS:
        r = Results()
        try:
            if check is placeholders.check:
                check(code, r, verbose)
            else:
                check(code, r)
        except Exception as err:
            r.error(f"the check itself failed: {type(err).__name__}: {err}")
        shown = [(l, m) for l, m in r.items if l != 'INFO' or verbose]
        errors = sum(1 for l, _ in r.items if l == 'ERROR')
        warns = sum(1 for l, _ in r.items if l == 'WARN')
        totals['ERROR'] += errors
        totals['WARN'] += warns
        status = 'ok' if not errors and not warns else ', '.join(
                    f"{n} {w}" for n, w in ((errors, 'errors'), (warns, 'warnings')) if n)
        print(f"== {title}: {status}")
        for level, msg in shown:
            print(f"   {level:5} {msg}")
    print(f"{totals['ERROR']} errors, {totals['WARN']} warnings")
    return 1 if totals['ERROR'] else 0


if __name__ == '__main__':
    sys.exit(main())
