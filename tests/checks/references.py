'''
Names the code uses that don't exist. Each one raises NameError/AttributeError when its
line runs. With the 'from x import *' imports expanded to the names of x:
    undefined names                 (needs pyflakes, skipped if it isn't installed)
    module.name                     'from . import utils_cf as x' ... x.name, name not in the module
    self.name in the flow classes   not a method or attribute of any Configure/Repairs flow
                                    class and not a HA flow attribute
Code after a return/raise in the same block is not checked (it never runs).
'''
from __future__ import annotations

import ast
import re
from pathlib import Path

from .common import reachable_walk

FLOW_FILES = ('config_flow.py', 'repairs.py', 'configure/')
HA_FLOW_ATTRS = {
    'async_show_form', 'async_show_menu', 'async_create_entry', 'async_abort',
    'async_show_progress', 'async_show_progress_done', 'async_external_step',
    'async_update_reload_and_abort', 'async_set_unique_id', 'hass', 'config_entry',
    'context', 'flow_id', 'handler', 'source', 'show_advanced_options', 'cur_step',
    'async_remove', 'add_suggested_values_to_schema', 'async_step_init',
    '_abort_if_unique_id_configured', 'async_get_options_flow', 'issue_id', 'data',
    'init_step', 'async_step_user', 'async_step_reauth', 'async_step_reconfigure',
    'options', 'logger', '__init__', '_get_reconfigure_entry', '_get_reauth_entry',
}
# support/test_controls.py: the controls that are commented out ('# NAME = ...') until a
# test needs them, the code that reads them only runs when the test is enabled
TEST_CONTROLS = 'support/test_controls.py'


def module_of(pkg_root, rel, level, module):
    '''The file (relative to the package) of a relative import, or None'''
    if not level:
        return None
    parts = Path(rel).parent.parts
    parts = parts[:len(parts) - (level - 1)] if level > 1 else parts
    target = list(parts) + (module.split('.') if module else [])
    base = pkg_root.joinpath(*target) if target else pkg_root
    if base.with_suffix('.py').exists():
        return str(base.with_suffix('.py').relative_to(pkg_root))
    if (base / '__init__.py').exists():
        return str((base / '__init__.py').relative_to(pkg_root))
    return None


class Names:
    def __init__(self, code):
        self.code = code
        self._names = {}

    def names(self, rel, seen=None):
        '''The top-level names of a module, star imports included'''
        if rel in self._names:
            return self._names[rel]
        seen = seen or set()
        seen.add(rel)
        out = set()
        for node in self.code.ast.get(rel, ast.Module(body=[])).body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                out.add(node.name)
            elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                for t in (node.targets if isinstance(node, ast.Assign) else [node.target]):
                    for n in ast.walk(t):
                        if isinstance(n, ast.Name):
                            out.add(n.id)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                for a in node.names:
                    if a.name == '*':
                        m = module_of(self.code.pkg, rel, node.level, node.module)
                        if m and m not in seen:
                            out |= self.names(m, seen)
                    else:
                        out.add((a.asname or a.name).split('.')[0])
            elif isinstance(node, (ast.If, ast.Try)):
                for sub in ast.walk(node):
                    if isinstance(sub, (ast.FunctionDef, ast.ClassDef)):
                        out.add(sub.name)
                    elif isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Store):
                        out.add(sub.id)
        self._names[rel] = out
        return out

    def module_aliases(self, rel):
        '''{alias: module} of the 'from . import x [as y]' imports of package modules'''
        out = {}
        for node in ast.walk(self.code.ast.get(rel, ast.Module(body=[]))):
            if isinstance(node, ast.ImportFrom) and node.level:
                for a in node.names:
                    if a.name == '*':
                        continue
                    sub = f"{node.module}.{a.name}" if node.module else a.name
                    m = module_of(self.code.pkg, rel, node.level, sub)
                    if m:
                        out[a.asname or a.name] = m
        return out

    def flow_attrs(self):
        '''Methods and attributes (self.x = ..., class level x = ...) of the flow classes'''
        out = set()
        for rel, tree in self.code.ast.items():
            if not rel.startswith(FLOW_FILES):
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for sub in node.body:
                        if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            out.add(sub.name)
                        elif isinstance(sub, (ast.Assign, ast.AnnAssign)):
                            for t in (sub.targets if isinstance(sub, ast.Assign) else [sub.target]):
                                if isinstance(t, ast.Name):
                                    out.add(t.id)
                if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                    for t in (node.targets if isinstance(node, ast.Assign) else [node.target]):
                        if (isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name)
                                and t.value.id == 'self'):
                            out.add(t.attr)
                # setattr(Class, f"async_step_open_{x}", ...) adds steps by prefix
                if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                        and node.func.id == 'setattr' and len(node.args) >= 2
                        and isinstance(node.args[1], ast.JoinedStr)
                        and node.args[1].values and isinstance(node.args[1].values[0], ast.Constant)):
                    out.add(node.args[1].values[0].value + '*')
        return out


def commented_test_controls(code):
    text = code.files.get(TEST_CONTROLS, '')
    return set(re.findall(r'^#\s*([A-Z][A-Z0-9_]+)\s*=', text, re.M))


def undefined_names(code, names, r):
    try:
        from pyflakes import api as pyflakes_api
        from pyflakes import messages as pyflakes_messages
    except ImportError:
        r.info('pyflakes is not installed, undefined names are not checked (pip install pyflakes)')
        return
    for rel, text in code.files.items():
        if rel not in code.ast:
            continue
        # Expand the star imports so pyflakes knows the names
        lines = text.split('\n')
        for node in code.ast[rel].body:
            if isinstance(node, ast.ImportFrom) and any(a.name == '*' for a in node.names):
                m = module_of(code.pkg, rel, node.level, node.module)
                if m:
                    star = sorted(n for n in names.names(m) if not n.startswith('_'))
                    lines[node.lineno - 1] = (f"from {'.' * node.level}{node.module or ''} import ("
                                              + ', '.join(star) + ')')
                    for i in range(node.lineno, node.end_lineno):
                        lines[i] = ''
        msgs = []

        class Reporter:
            def flake(self, msg):
                msgs.append(msg)

            def syntaxError(self, *args):
                pass

            def unexpectedError(self, *args):
                pass

        pyflakes_api.check('\n'.join(lines), rel, Reporter())
        for msg in msgs:
            if isinstance(msg, pyflakes_messages.UndefinedName):
                r.error(f"{rel}:{msg.lineno}: undefined name {msg.message_args[0]}")


def check(code, r):
    names = Names(code)
    undefined_names(code, names, r)
    test_controls = commented_test_controls(code)
    found = set()
    for rel, tree in code.ast.items():
        aliases = names.module_aliases(rel)
        for node in reachable_walk(tree):
            if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
                    and node.value.id in aliases and isinstance(node.ctx, ast.Load)):
                m = aliases[node.value.id]
                if node.attr in names.names(m) or node.attr.startswith('__'):
                    continue
                if m == TEST_CONTROLS and node.attr in test_controls:
                    continue
                found.add((rel, node.lineno, f"{node.value.id}.{node.attr} is not defined in {m}"))

    attrs = names.flow_attrs()
    prefixes = tuple(m[:-1] for m in attrs if m.endswith('*')) or ('\0',)
    for rel, tree in code.ast.items():
        if not rel.startswith(FLOW_FILES):
            continue
        # The flow classes, and the step functions that get self (setattr loops)
        scopes = [n for n in ast.walk(tree)
                  if isinstance(n, ast.ClassDef) and any(w in n.name for w in ('Flow', 'Steps', 'Repair'))]
        scopes += [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                   and n.args.args and n.args.args[0].arg == 'self']
        for scope in scopes:
            for node in reachable_walk(scope):
                if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
                        and node.value.id == 'self' and isinstance(node.ctx, ast.Load)
                        and node.attr not in attrs and node.attr not in HA_FLOW_ATTRS
                        and not node.attr.startswith('__') and not node.attr.startswith(prefixes)):
                    found.add((rel, node.lineno, f"self.{node.attr} is not a method or attribute "
                                                 f"of the flow classes"))
    for rel, line, msg in sorted(found):
        r.error(f"{rel}:{line}: {msg}")
