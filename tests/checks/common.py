'''The iCloud3 code and texts the static checks read (no Home Assistant needed)'''
from __future__ import annotations

import ast
import json
from pathlib import Path

PKG = 'custom_components/icloud3'


class Code:
    def __init__(self, root):
        self.root = Path(root)
        self.pkg = self.root / PKG
        if not (self.pkg / 'manifest.json').exists():
            raise SystemExit(f"{self.pkg} is not the iCloud3 integration (no manifest.json)")
        self.files = {}         # path relative to the package: text
        for p in sorted(self.pkg.rglob('*.py')):
            if '__pycache__' not in p.parts:
                self.files[str(p.relative_to(self.pkg))] = p.read_text(encoding='utf-8')
        self.ast = {}
        self.syntax_errors = []
        for rel, text in self.files.items():
            try:
                self.ast[rel] = ast.parse(text, rel)
            except SyntaxError as err:
                self.syntax_errors.append((rel, err))

    def json(self, rel):
        return json.loads((self.pkg / rel).read_text(encoding='utf-8'))

    @property
    def strings(self):
        return self.json('strings.json')

    def translation_files(self):
        return sorted((self.pkg / 'translations').glob('*.json'))


class Results:
    '''(level, message) findings. ERROR fails the check, WARN and INFO don't.'''
    def __init__(self):
        self.items = []

    def add(self, level, msg):
        self.items.append((level, msg))

    def error(self, msg):
        self.add('ERROR', msg)

    def warn(self, msg):
        self.add('WARN', msg)

    def info(self, msg):
        self.add('INFO', msg)


def flatten(d, prefix=''):
    out = {}
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            out.update(flatten(v, key))
        else:
            out[key] = v
    return out


def reachable_walk(node):
    '''ast.walk without the statements that follow a return/raise/continue/break in the
    same block (code that never runs)'''
    todo = [node]
    while todo:
        n = todo.pop()
        yield n
        for field, value in ast.iter_fields(n):
            if isinstance(value, list):
                items = []
                for item in value:
                    items.append(item)
                    if isinstance(item, (ast.Return, ast.Raise, ast.Continue, ast.Break)):
                        break
                todo.extend(i for i in reversed(items) if isinstance(i, ast.AST))
            elif isinstance(value, ast.AST):
                todo.append(value)
