'''
Text keys of strings.json: the ones the code asks for and strings.json doesn't have
(ERROR, the screen shows the raw key or the option value), and the ones no code refers to
(WARN, dead texts).

Missing: selector translation_key (select(..., 'key'), translation_key='key'), the options
of a list menu (async_show_menu(menu_options=[...])), MENU_TREE = {menu: [options]}. The
form/menu step texts, error keys and tr() keys are checked by placeholders.py.

Unused: a key is used when its id (the step id, field name, error key, selector key or
option, issue key) is a string in the code, starts with the constant start of an
f-string, or is the name of an async_step_<id> method. That finds dead texts, not every
unused one (a common word like 'menu' is always "used").
'''
from __future__ import annotations

import ast
import re

from .common import flatten, reachable_walk

FLOW_FILES = ('config_flow.py', 'repairs.py', 'configure/')
STEP_PARTS = ('title', 'description', 'submit', 'data', 'data_description', 'sections',
              'menu_options', 'menu_option_descriptions')


def _literal(node):
    '''(text, is_prefix) of a str constant or an f-string with a constant start'''
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value, False
    if (isinstance(node, ast.JoinedStr) and node.values
            and isinstance(node.values[0], ast.Constant)):
        return node.values[0].value, True
    return None, False


def missing(code, r):
    paths = set()
    def walk(obj, path=()):
        paths.add('.'.join(path))
        if isinstance(obj, dict):
            for k, v in obj.items():
                walk(v, path + (k,))
    walk(code.strings)
    found = set()

    def need(rel, line, key, prefix=False):
        if prefix and not any(p.startswith(key) for p in paths):
            found.add((rel, line, f"no text key starts with {key}"))
        elif not prefix and key not in paths:
            found.add((rel, line, f"{key} is not in strings.json"))

    for rel, tree in code.ast.items():
        if not rel.startswith(FLOW_FILES):
            continue
        for node in reachable_walk(tree):
            if isinstance(node, ast.Call):
                fname = (node.func.attr if isinstance(node.func, ast.Attribute)
                         else node.func.id if isinstance(node.func, ast.Name) else '')
                tkey = next((k.value for k in node.keywords if k.arg == 'translation_key'), None)
                if tkey is None and fname == 'select' and len(node.args) > 1:
                    tkey = node.args[1]
                if tkey is not None and fname not in ('async_create_issue', 'post_repair_issue'):
                    text, _ = _literal(tkey)
                    if text and (fname == 'select' or 'Selector' in fname):
                        need(rel, node.lineno, f"selector.{text}.options.", prefix=True)
                if fname == 'async_show_menu' and not rel.startswith('repairs'):
                    kw = {k.arg: k.value for k in node.keywords}
                    step_id, _ = _literal(kw['step_id']) if 'step_id' in kw else (None, False)
                    opts = kw.get('menu_options')
                    if step_id and isinstance(opts, (ast.List, ast.Tuple)):
                        for opt in opts.elts:
                            text, _ = _literal(opt)
                            if text:
                                need(rel, node.lineno, f"options.step.{step_id}.menu_options.{text}")
            # MENU_TREE = {menu step_id: [menu options]}
            if (isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
                    and node.targets[0].id == 'MENU_TREE' and isinstance(node.value, ast.Dict)):
                for k, v in zip(node.value.keys, node.value.values):
                    for opt in getattr(v, 'elts', []):
                        if isinstance(k, ast.Constant) and isinstance(opt, ast.Constant):
                            need(rel, node.lineno, f"options.step.{k.value}.menu_options.{opt.value}")
    for rel, line, msg in sorted(found):
        r.error(f"{rel}:{line}: {msg}")


def code_words(code):
    '''(strings, prefixes, suffixes) the code refers to text keys with'''
    words, prefixes, suffixes = set(), set(), set()
    for tree in code.ast.values():
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float, str)) \
                    and not isinstance(node.value, bool):
                # selector option keys can only have a-z 0-9 _ -: '.cn,GCJ02' -> cn_gcj02, .25 -> 0_25
                words.add(re.sub(r'_{2,}', '_', re.sub(r'[^a-z0-9_-]', '_', str(node.value).lower())).strip('_-'))
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                v = node.value
                words.add(v)
                words.update(v.split('.'))
                if v.endswith('_') and len(v) >= 3:
                    prefixes.add(v)
                if v.startswith('_') and len(v) >= 3:
                    suffixes.add(v)
            elif isinstance(node, ast.JoinedStr):
                text, _ = _literal(node)
                if text and len(text.split('.')[-1]) >= 3:
                    prefixes.add(text.split('.')[-1])
                last = node.values[-1] if node.values else None
                if (isinstance(last, ast.Constant) and len(node.values) > 1
                        and last.value.startswith('_') and len(last.value) >= 3):
                    suffixes.add(last.value)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                words.add(node.name)
                if node.name.startswith('async_step_'):
                    words.add(node.name[len('async_step_'):])
    return words, tuple(prefixes), tuple(suffixes)


def is_used(ident, words, prefixes, suffixes):
    if ident in words or ident.startswith(prefixes) or ident.endswith(suffixes):
        return True
    # tr_cnt('key') shows key_one / key_other
    for plural in ('_one', '_other', '_zero'):
        if ident.endswith(plural) and ident[:-len(plural)] in words:
            return True
    return False


def ids_of(key):
    '''[(path, id)] of a flattened strings.json key: the parts that the code must name'''
    p = key.split('.')
    if any(x.startswith('_comment') for x in p):
        return []
    out = []
    def step(base, rest):
        # rest = [step_id, part, ...]
        if not rest:
            return
        out.append((f"{base}.{rest[0]}", rest[0]))
        if len(rest) >= 3 and rest[1] in ('data', 'data_description', 'menu_options',
                                          'menu_option_descriptions'):
            out.append((f"{base}.{rest[0]}.{rest[1]}.{rest[2]}", rest[2]))
        if len(rest) >= 3 and rest[1] == 'sections':
            out.append((f"{base}.{rest[0]}.sections.{rest[2]}", rest[2]))
            if len(rest) >= 5 and rest[3] in ('data', 'data_description'):
                out.append((f"{base}.{rest[0]}.sections.{rest[2]}.{rest[3]}.{rest[4]}", rest[4]))
    if p[0] in ('config', 'options') and len(p) >= 3:
        if p[1] == 'step':
            step(f"{p[0]}.step", p[2:])
        elif p[1] in ('error', 'abort', 'progress', 'create_entry'):
            out.append((f"{p[0]}.{p[1]}.{p[2]}", p[2]))
    elif p[0] == 'selector' and len(p) >= 2:
        out.append((f"selector.{p[1]}", p[1]))
        if len(p) >= 4 and p[2] == 'options':
            out.append((f"selector.{p[1]}.options.{p[3]}", p[3]))
    elif p[0] == 'issues' and len(p) >= 2:
        out.append((f"issues.{p[1]}", p[1]))
        if len(p) >= 5 and p[2] == 'fix_flow':
            if p[3] == 'step':
                step(f"issues.{p[1]}.fix_flow.step", p[4:])
            elif p[3] in ('error', 'abort'):
                out.append((f"issues.{p[1]}.fix_flow.{p[3]}.{p[4]}", p[4]))
    return out


def unused(code, r):
    words, prefixes, suffixes = code_words(code)
    unused_paths = set()
    for key in flatten(code.strings):
        for path, ident in ids_of(key):
            if not is_used(ident, words, prefixes, suffixes):
                # the shortest unused path of the key (a step, not each of its texts)
                unused_paths.add(path)
                break
    # One line per section: options.error: a, b, c
    sections = {}
    for path in sorted(unused_paths):
        section, ident = path.rsplit('.', 1)
        sections.setdefault(section, []).append(ident)
    for section, idents in sorted(sections.items()):
        r.warn(f"{section}: {len(idents)} no code refers to: {', '.join(idents)}")
