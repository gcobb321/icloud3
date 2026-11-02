'''
The {placeholders} of the strings.json texts against the description_placeholders the
code passes to the HA flow screens (config, options and repair fix flows).

What the HA frontend (20260930.x: show-dialog-config-flow.ts, show-dialog-options-flow.ts,
show-dialog-repair-flow.ts, step-flow-menu.ts) passes to localize():
    form  title, description, data, data_description, sections.*  - step placeholders
          submit                                                   - none
    menu  title                                                    - NONE (config & options)
          description, menu_options (list menus), menu_option_descriptions - step placeholders
          menu_options of a {option: label} menu                   - not used, the label is shown
    error <flow>.error.<key> on a form                             - the form's placeholders
    abort <flow>.abort.<reason>                                    - the abort placeholders
    repair fix_flow steps                                          - issue + step placeholders
A {placeholder} that is not in the values makes formatjs fail and the frontend displays
'Translation [formatjs Error: MISSING_VALUE] ...' in place of the text.

The utils_cf.tr / tr_cnt / tr_path texts (if the code has them) are filled in by Python
(str.replace), a missing keyword leaves '{name}' in the text. They are checked too.

Also: a form/menu step without texts in strings.json, and a displayed error key that is
not in options.error (the screen shows the raw key).

Levels:
    ERROR  the placeholder is never passed on this code path (or the frontend never passes
           placeholders to this string)
    WARN   only passed on some branches (if/for), or only by a menu row that may be absent
    INFO   the placeholders come from a value the script can't follow
'''

import ast
import json
import re
from collections import defaultdict

from .common import PKG
PH_RE = re.compile(r'\{(\w+)\}')
SHOW_CALLS = {'async_show_form', 'async_show_menu', 'async_show_list_menu', 'async_abort',
              'async_show_progress', 'async_create_entry'}

# Keys show_form_placeholders (utils_cf) adds to every form of the flows that override
# async_show_form with it. They are set by the action that displays the message.
WRAPPER_ATTRS = ('header_placeholders', 'form_placeholders')


#----------------------------------------------------------------------------------------
class Source:
    def __init__(self, code):
        self.code = code

    def files(self):
        return [f"{PKG}/{rel}" for rel in self.code.files]

    def read(self, path):
        rel = path[len(PKG) + 1:]
        if rel in self.code.files:
            return self.code.files[rel]
        return (self.code.pkg / rel).read_text(encoding='utf-8')


#----------------------------------------------------------------------------------------
class Keys:
    '''possible: keys on some path, sure: keys on every path, unknown: unfollowed values'''
    def __init__(self, possible=(), sure=(), unknown=(), patterns=()):
        self.possible, self.sure, self.unknown = set(possible), set(sure), list(unknown)
        self.patterns = set(patterns)       # f-string keys (f"device_{slot}" -> device_\w+)

    def add(self, other, sure=True):
        self.possible |= other.possible
        self.patterns |= other.patterns
        if sure:
            self.sure |= other.sure
        self.unknown += other.unknown
        return self

    @staticmethod
    def alternatives(alts):
        alts = [a for a in alts if a is not None]
        if not alts:
            return Keys()
        k = Keys(set().union(*[a.possible for a in alts]),
                 set.intersection(*[a.sure for a in alts]))
        for a in alts:
            k.unknown += a.unknown
            k.patterns |= a.patterns
        return k

    def matches(self, key):
        return any(re.fullmatch(p, key) for p in self.patterns)


class Func:
    def __init__(self, node, path, cls):
        self.node, self.path, self.cls = node, path, cls
        self.params = [a.arg for a in node.args.args + node.args.kwonlyargs]
        self.parent = {}
        for parent in ast.walk(node):
            for child in ast.iter_child_nodes(parent):
                self.parent[child] = parent

    def is_conditional(self, node):
        '''The node is inside an if/for/while/try/with or a nested function'''
        p = self.parent.get(node)
        while p is not None and p is not self.node:
            if isinstance(p, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try,
                              ast.IfExp, ast.comprehension, ast.FunctionDef,
                              ast.AsyncFunctionDef, ast.Lambda)):
                return True
            p = self.parent.get(p)
        return False


class Code:
    def __init__(self, src):
        self.funcs = defaultdict(list)          # name -> [Func]
        self.attr_assigns = defaultdict(list)   # self.<attr> -> [(Func, value node)]
        self.attr_keys = defaultdict(list)      # self.<attr>[k] = / .update() -> [(Func, node, Keys)]
        self.consts = {}                        # NAME = 'str' module constants
        self.modules = {}
        for path in src.files():
            try:
                tree = ast.parse(src.read(path), path)
            except SyntaxError:
                continue                        # reported by the imports check
            self.modules[path] = tree
            for node in tree.body:
                if (isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant)
                        and isinstance(node.value.value, str)):
                    for t in node.targets:
                        if isinstance(t, ast.Name):
                            self.consts[t.id] = node.value.value
            self._index(tree, path, None)
        for funcs in self.funcs.values():
            for f in funcs:
                self._index_attrs(f)

    def _index(self, node, path, cls):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                self._index(child, path, child.name)
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.funcs[child.name].append(Func(child, path, cls))
                self._index(child, path, cls)

    def _index_attrs(self, f):
        for node in ast.walk(f.node):
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if _is_self_attr(t):
                        self.attr_assigns[t.attr].append((f, node.value))
                    elif isinstance(t, ast.Subscript) and _is_self_attr(t.value):
                        k = _const_str(t.slice, self.consts)
                        pat = _fstring_pattern(t.slice)
                        self.attr_keys[t.value.attr].append(
                            (f, node, Keys([k], [k]) if k else Keys(patterns=[pat]) if pat else
                                      Keys(unknown=[_src(t)])))
            elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == 'update' and _is_self_attr(node.func.value)
                    and node.args):
                self.attr_keys[node.func.value.attr].append((f, node, ('expr', node.args[0])))

    def enclosing(self, path, lineno):
        best = None
        for funcs in self.funcs.values():
            for f in funcs:
                if (f.path == path and f.node.lineno <= lineno <= f.node.end_lineno
                        and (best is None or f.node.lineno > best.node.lineno)):
                    best = f
        return best


def _is_self_attr(node):
    return (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
            and node.value.id == 'self')

def _const_str(node, consts):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name) and node.id in consts:
        return consts[node.id]
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.attr in consts:
        return consts[node.attr]                # aas.REPAIR_ISSUE_ACCT_LOCKED
    return None

def _src(node):
    try:
        return ast.unparse(node)[:80]
    except Exception:
        return type(node).__name__

def _fstring_pattern(node):
    if not isinstance(node, ast.JoinedStr):
        return None
    return ''.join(re.escape(v.value) if isinstance(v, ast.Constant) else r'\w+'
                    for v in node.values)

def _call_name(call):
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    if isinstance(call.func, ast.Name):
        return call.func.id
    return None

def _kwarg(call, name, pos=None):
    for kw in call.keywords:
        if kw.arg == name:
            return kw.value
    if pos is not None and len(call.args) > pos:
        return call.args[pos]
    return None


#----------------------------------------------------------------------------------------
class Resolver:
    '''Follows a placeholders expression to the dict keys it can have'''
    def __init__(self, code):
        self.code = code
        self.stack = []

    def expr(self, node, f, tuple_idx=None):
        key = (id(node), tuple_idx)
        if key in self.stack or len(self.stack) > 25:
            return Keys()
        self.stack.append(key)
        try:
            return self._expr(node, f, tuple_idx)
        finally:
            self.stack.pop()

    def _expr(self, node, f, tuple_idx):
        consts = self.code.consts
        if node is None or (isinstance(node, ast.Constant) and node.value is None):
            return Keys()
        if isinstance(node, ast.Tuple) and tuple_idx is not None:
            return self.expr(node.elts[tuple_idx], f) if tuple_idx < len(node.elts) else Keys()
        if isinstance(node, ast.Dict):
            k = Keys()
            for knode, vnode in zip(node.keys, node.values):
                if knode is None:
                    k.add(self.expr(vnode, f))
                else:
                    s = _const_str(knode, consts)
                    if s is None:
                        k.unknown.append(f"dict key {_src(knode)}")
                    else:
                        k.possible.add(s); k.sure.add(s)
            return k
        if isinstance(node, ast.DictComp):
            return Keys(unknown=[f"dict comprehension {_src(node)}"])
        if isinstance(node, (ast.BoolOp, ast.IfExp)):
            parts = node.values if isinstance(node, ast.BoolOp) else [node.body, node.orelse]
            return Keys.alternatives([self.expr(p, f, tuple_idx) for p in parts])
        if isinstance(node, ast.Call):
            name = _call_name(node)
            if name == 'dict':
                k = Keys()
                for a in node.args:
                    k.add(self.expr(a, f))
                for kw in node.keywords:
                    if kw.arg is None:
                        k.add(self.expr(kw.value, f))
                    else:
                        k.possible.add(kw.arg); k.sure.add(kw.arg)
                return k
            if name in ('get', 'copy', 'pop') and isinstance(node.func, ast.Attribute):
                base = node.func.value
                if name == 'copy':
                    return self.expr(base, f, tuple_idx)
                if (isinstance(base, ast.Attribute) and _is_self_attr(base)
                        and node.args and _const_str(node.args[0], consts)):
                    # self.confirm_action.get('done_placeholders')
                    return self.dict_item(base.attr, _const_str(node.args[0], consts))
                if (_is_self_attr(base) is False and isinstance(base, ast.Attribute)
                        and base.attr == '__dict__' and node.args):
                    attr = _const_str(node.args[0], consts)
                    return self.attr(attr) if attr else Keys(unknown=[_src(node)])
                return Keys(unknown=[_src(node)])
            funcs = self.code.funcs.get(name, [])
            if not funcs:
                return Keys(unknown=[f"call {_src(node)}"])
            alts = []
            for g in funcs:
                for ret in ast.walk(g.node):
                    if isinstance(ret, ast.Return) and self._own(g, ret):
                        alts.append(self.expr(ret.value, g, tuple_idx))
            return Keys.alternatives(alts)
        if isinstance(node, ast.Name):
            return self.name(node.id, f, node, tuple_idx)
        if _is_self_attr(node):
            return self.attr(node.attr)
        return Keys(unknown=[_src(node)])

    def _own(self, g, node):
        '''node is in g and not in a function nested in g'''
        p = g.parent.get(node)
        while p is not None and p is not g.node:
            if isinstance(p, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                return False
            p = g.parent.get(p)
        return True

    def name(self, ident, f, use_node, tuple_idx):
        if f is None:
            return Keys(unknown=[ident])
        assigns, extra = [], Keys()
        for node in ast.walk(f.node):
            if not self._own(f, node) or getattr(node, 'lineno', 0) > use_node.lineno:
                continue
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                targets = [e for t in targets
                                for e in (t.elts if isinstance(t, ast.Tuple) else [t])
                                if not (isinstance(t, ast.Tuple) and isinstance(e, ast.Name))] + \
                          [(i, e) for t in targets if isinstance(t, ast.Tuple)
                                for i, e in enumerate(t.elts) if isinstance(e, ast.Name)]
                for t in targets:
                    if isinstance(t, tuple):
                        i, e = t
                        if e.id == ident:
                            assigns.append(self.expr(node.value, f, i))
                    elif isinstance(t, ast.Name) and t.id == ident:
                        assigns.append(self.expr(node.value, f, tuple_idx))
                    elif (isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name)
                            and t.value.id == ident):
                        k = _const_str(t.slice, self.code.consts)
                        pat = _fstring_pattern(t.slice)
                        extra.add(Keys([k], [k]) if k else
                                  Keys(patterns=[pat]) if pat else
                                  Keys(unknown=[f"{ident}[{_src(t.slice)}]"]),
                                  sure=not f.is_conditional(node))
            elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == 'update' and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == ident and node.args):
                extra.add(self.expr(node.args[0], f), sure=not f.is_conditional(node))
        if not assigns:
            if ident in f.params:
                return Keys(unknown=[f"parameter {ident} of {f.node.name}"]).add(extra)
            return Keys(unknown=[ident]).add(extra)
        return Keys.alternatives(assigns).add(extra)

    def attr(self, attr):
        alts = [self.expr(value, g) for g, value in self.code.attr_assigns.get(attr, [])
                    if not (isinstance(value, ast.Constant) and value.value is None)]
        k = Keys.alternatives(alts)
        for g, node, keys in self.code.attr_keys.get(attr, []):
            if isinstance(keys, tuple):
                keys = self.expr(keys[1], g)
            k.add(keys, sure=False)
        return k

    def dict_item(self, attr, item):
        '''self.<attr>['item'] values of the dicts assigned to self.<attr>'''
        alts = []
        for g, value in self.code.attr_assigns.get(attr, []):
            if isinstance(value, ast.Dict):
                for knode, vnode in zip(value.keys, value.values):
                    if knode is not None and _const_str(knode, self.code.consts) == item:
                        alts.append(self.expr(vnode, g))
        k = Keys.alternatives(alts)
        k.sure = set()
        return k


#----------------------------------------------------------------------------------------
class Site:
    def __init__(self, kind, step_id, path, lineno, func, keys, menu=None):
        self.kind, self.step_id, self.path, self.lineno = kind, step_id, path, lineno
        self.func, self.keys, self.menu = func, keys, menu

    def where(self):
        return f"{self.path.replace(PKG + '/', '')}:{self.lineno}"


def flows_of(site):
    '''The strings.json flows the call site's screen is displayed in'''
    if site.func.cls is None:
        return ['options', 'config']
    cls = site.func.cls
    if 'Repair' in cls:
        return ['repairs']
    if cls == 'iCloud3_ConfigFlow':
        return ['config']
    if cls == 'iCloud3_OptionsFlowHandler':
        return ['options']
    # configure/screens mixins: Configure (options), the reauth config flow and repairs
    return ['options', 'config', 'repairs']


def step_ids(code, call, func, arg):
    s = _const_str(arg, code.consts) if arg is not None else None
    if s:
        return [s]
    if isinstance(arg, ast.Name) and func and arg.id in func.params:
        pos = func.params.index(arg.id)
        ids = set()
        for funcs in code.funcs.values():
            for g in funcs:
                for c in ast.walk(g.node):
                    if isinstance(c, ast.Call) and _call_name(c) == func.node.name:
                        offset = 1 if func.params and func.params[0] == 'self' else 0
                        a = _kwarg(c, arg.id, pos - offset)
                        v = _const_str(a, code.consts) if a is not None else None
                        if v:
                            ids.add(v)
        return sorted(ids)
    return []


def list_menu_keys(code, r):
    '''The keys utils_cf.async_show_list_menu adds to the placeholders it is given'''
    k = Keys()
    for g in code.funcs.get('async_show_list_menu', []):
        for c in ast.walk(g.node):
            if isinstance(c, ast.Call) and _call_name(c) == 'async_show_menu':
                inner = r.expr(_kwarg(c, 'description_placeholders'), g)
                k.possible |= inner.possible; k.sure |= inner.sure
    return k


def find_sites(code, report):
    r = Resolver(code)
    sites = []
    for path, tree in code.modules.items():
        for call in ast.walk(tree):
            if not isinstance(call, ast.Call):
                continue
            name = _call_name(call)
            if name not in SHOW_CALLS:
                continue
            f = code.enclosing(path, call.lineno)
            if f is None or f.node.name in (name, 'async_show_list_menu'):
                continue                    # the async_show_form overrides, the list menu helper
            if name == 'async_show_list_menu':
                ids = step_ids(code, call, f, _kwarg(call, 'step_id', 1))
                keys = r.expr(_kwarg(call, 'placeholders', 4), f).add(list_menu_keys(code, r))
                kind, menu = 'menu', 'dict'
            elif name == 'async_abort':
                ids = step_ids(code, call, f, _kwarg(call, 'reason', 0))
                if not ids:
                    continue                # flow.async_abort(flow_id) of another flow
                keys = r.expr(_kwarg(call, 'description_placeholders'), f)
                kind, menu = 'abort', None
            elif name == 'async_create_entry':
                ids = step_ids(code, call, f, _kwarg(call, 'description'))
                if not ids:
                    continue
                keys = r.expr(_kwarg(call, 'description_placeholders'), f)
                kind, menu = 'create_entry', None
            else:
                ids = step_ids(code, call, f, _kwarg(call, 'step_id'))
                keys = r.expr(_kwarg(call, 'description_placeholders'), f)
                kind = {'async_show_form': 'form', 'async_show_menu': 'menu',
                        'async_show_progress': 'progress'}[name]
                menu = None
                if kind == 'menu':
                    mo = _kwarg(call, 'menu_options')
                    menu = 'dict' if isinstance(mo, ast.Dict) else 'list'
            if not ids:
                report('INFO', f"{path.replace(PKG + '/', '')}:{call.lineno} {name}: step_id "
                               f"{_src(_kwarg(call, 'step_id') or call)} not followed")
            for step_id in ids:
                sites.append(Site(kind, step_id, path, call.lineno, f, keys, menu))
    return sites, r


#----------------------------------------------------------------------------------------
def find_issue_placeholders(code, resolver):
    '''
    {translation_key: Keys} of the Repairs issues: the translation_key=CONST,
    translation_placeholders=... calls and the translation_key = CONST assignment followed
    by translation_placeholders = {...}. post_repair_issue adds 'fname' when there is a
    'title'. The frontend merges them into every fix_flow step, abort and create_entry.
    '''
    found = defaultdict(list)
    for path, tree in code.modules.items():
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                tk = _kwarg(node, 'translation_key')
                key = _const_str(tk, code.consts) if tk is not None else None
                if key and _call_name(node) != 'select':
                    f = code.enclosing(path, node.lineno)
                    found[key].append(resolver.expr(_kwarg(node, 'translation_placeholders'), f))
            elif isinstance(node, (ast.If, ast.Module, ast.FunctionDef, ast.AsyncFunctionDef)):
                body = node.body
                for a, b in zip(body, body[1:]):
                    if (isinstance(a, ast.Assign) and isinstance(b, ast.Assign)
                            and [_src(t) for t in a.targets] == ['translation_key']
                            and [_src(t) for t in b.targets] == ['translation_placeholders']):
                        key = _const_str(a.value, code.consts)
                        if key:
                            f = code.enclosing(path, a.lineno)
                            found[key].append(resolver.expr(b.value, f))
    issues = {}
    for key, alts in found.items():
        k = Keys.alternatives(alts)
        if 'title' in k.possible:
            k.possible.add('fname')
            if 'title' in k.sure:
                k.sure.add('fname')
        issues[key] = k
    return issues


def strings_of_step(step, kind, menu):
    '''[(field path, text, frontend passes the placeholders)]'''
    out = []
    def add(field, text, passed):
        if isinstance(text, str):
            out.append((field, text, passed))
    if kind == 'form':
        add('title', step.get('title'), True)
        add('description', step.get('description'), True)
        add('submit', step.get('submit'), False)
        for sect in ('data', 'data_description'):
            for k, v in (step.get(sect) or {}).items():
                add(f"{sect}.{k}", v, True)
        for sname, sect in (step.get('sections') or {}).items():
            add(f"sections.{sname}.name", sect.get('name'), True)
            add(f"sections.{sname}.description", sect.get('description'), True)
            for ss in ('data', 'data_description'):
                for k, v in (sect.get(ss) or {}).items():
                    add(f"sections.{sname}.{ss}.{k}", v, True)
    elif kind == 'menu':
        add('title', step.get('title'), False)
        add('description', step.get('description'), True)
        for k, v in (step.get('menu_option_descriptions') or {}).items():
            add(f"menu_option_descriptions.{k}", v, True)
        if menu == 'list':
            for k, v in (step.get('menu_options') or {}).items():
                add(f"menu_options.{k}", v, True)
    elif kind == 'progress':
        add('title', step.get('title'), False)
    return out


def check_all(code_obj, verbose=False):
    src = Source(code_obj)
    strings = json.loads(src.read(f"{PKG}/strings.json"))
    results = []
    def report(level, msg):
        results.append((level, msg))

    code = Code(src)
    sites, resolver = find_sites(code, report)
    wrapper = Keys.alternatives([resolver.attr(a) for a in WRAPPER_ATTRS])
    wrapper.sure = set()
    overrides = {f.cls for f in code.funcs.get('async_show_form', [])
                    if any('show_form_placeholders' in _src(n) for n in ast.walk(f.node)
                            if isinstance(n, ast.Call))}

    # Which flows' strings each step id has
    def step_strings(flow, step_id, kind):
        if flow in ('config', 'options'):
            sect = {'abort': 'abort', 'create_entry': 'create_entry'}.get(kind, 'step')
            s = strings.get(flow, {}).get(sect, {}).get(step_id)
            return [(f"{flow}.{sect}.{step_id}", s)] if s is not None else []
        found = []
        sect = {'abort': 'abort', 'create_entry': 'create_entry'}.get(kind, 'step')
        for issue, idef in strings.get('issues', {}).items():
            s = (idef.get('fix_flow') or {}).get(sect, {}).get(step_id)
            if s is not None:
                found.append((f"issues.{issue}.fix_flow.{sect}.{step_id}", s))
        return found

    issue_keys = find_issue_placeholders(code, resolver)
    for issue, idef in strings.get('issues', {}).items():
        ik = issue_keys.get(issue)
        if ik is None:
            report('INFO', f"issues.{issue}: no code posts this translation_key")
            continue
        for field in ('title', 'description'):
            used = set(PH_RE.findall(idef.get(field, '')))
            missing = used - ik.possible
            if missing:
                report('WARN' if ik.unknown else 'ERROR',
                       f"issues.{issue}.{field} uses {sorted(missing)}, not in the issue's translation_placeholders")
            elif used - ik.sure:
                report('WARN', f"issues.{issue}.{field} {sorted(used - ik.sure)} not in every post of the issue")

    seen_steps = set()
    repair_steps = defaultdict(list)
    for site in sites:
        keys = Keys(site.keys.possible, site.keys.sure, site.keys.unknown, site.keys.patterns)
        if site.kind == 'form' and (site.func.cls in overrides or site.func.cls is None
                                    or site.func.cls.startswith('OptionsFlow_')):
            keys.add(wrapper, sure=False)
        any_found = False
        for flow in flows_of(site):
            for spath, sdef in step_strings(flow, site.step_id, site.kind):
                any_found = True
                seen_steps.add(spath)
                if isinstance(sdef, str):
                    fields = [('', sdef, True)]
                else:
                    fields = strings_of_step(sdef, site.kind, site.menu)
                if flow == 'repairs':
                    # The fix flow class of an issue isn't followed, the step's keys are
                    # the union of the repairs call sites displaying it
                    repair_steps[spath].append((site, keys, fields))
                    continue
                fkeys = keys
                for field, text, passed in fields:
                    used = set(PH_RE.findall(text))
                    if not used:
                        continue
                    keys = fkeys
                    label = f"{spath}{'.' + field if field else ''}"
                    if not passed:
                        report('ERROR', f"{label} uses {sorted(used)} but the frontend passes no "
                                        f"placeholders to a {site.kind} {field.split('.')[0]}  [{site.where()}]")
                        continue
                    missing = {u for u in used - keys.possible if not keys.matches(u)}
                    if missing:
                        lvl = 'WARN' if keys.unknown else 'ERROR'
                        extra = f" (unfollowed: {'; '.join(keys.unknown[:3])})" if keys.unknown else ''
                        report(lvl, f"{label} uses {sorted(missing)}, not passed  [{site.where()}]{extra}")
                    maybe = ((used & keys.possible) | {u for u in used if keys.matches(u)}) - keys.sure
                    row = field.startswith('menu_option')
                    if maybe and (verbose or not row):
                        report('WARN', f"{label} {sorted(maybe)} only passed on some branches"
                                       f"{' (row may be absent)' if row else ''}  [{site.where()}]")
        if not any_found and site.kind in ('form', 'menu') and site.func.cls and 'Repair' in site.func.cls:
            pass
        elif not any_found and site.kind in ('form', 'menu') and site.step_id.startswith('async_step_'):
            report('ERROR', f"{site.kind} step_id {site.step_id!r} starts with 'async_step_': HA refuses "
                            f"the screen (UnknownStep) because the flow has no "
                            f"async_step_{site.step_id}  [{site.where()}]")
        elif not any_found and site.kind in ('form', 'menu'):
            report('ERROR', f"{site.kind} step_id {site.step_id!r} has no texts in strings.json "
                            f"({' or '.join(flows_of(site))}.step.{site.step_id}): the screen shows "
                            f"raw field names, and HA refuses the screen if the flow has no "
                            f"async_step_{site.step_id}  [{site.where()}]")

    for spath, entries in repair_steps.items():
        ik = issue_keys.get(spath.split('.')[1], Keys(unknown=['issue placeholders']))
        keys = Keys.alternatives([k for _s, k, _f in entries])
        keys.possible |= set().union(*[k.possible for _s, k, _f in entries])
        keys.add(ik)
        where = ', '.join(sorted({s.where() for s, _k, _f in entries}))
        for field, text, passed in entries[0][2]:
            used = set(PH_RE.findall(text))
            label = f"{spath}{'.' + field if field else ''}"
            if used and not passed:
                report('ERROR', f"{label} uses {sorted(used)} but the frontend passes no placeholders  [{where}]")
                continue
            missing = {u for u in used - keys.possible if not keys.matches(u)}
            if missing:
                extra = f" (unfollowed: {'; '.join(dict.fromkeys(keys.unknown))})" if keys.unknown else ''
                report('WARN' if keys.unknown else 'ERROR',
                       f"{label} uses {sorted(missing)}, not passed by the issue or the step  [{where}]{extra}")

    # Error texts with placeholders: where they are set
    for flow in ('config', 'options'):
        for ekey, text in strings.get(flow, {}).get('error', {}).items():
            used = set(PH_RE.findall(text))
            if not used:
                continue
            uses = []
            for path, tree in code.modules.items():
                for node in ast.walk(tree):
                    if isinstance(node, ast.Constant) and node.value == ekey:
                        uses.append(f"{path.replace(PKG + '/', '')}:{node.lineno}")
            report('INFO', f"{flow}.error.{ekey} needs {sorted(used)}; set at {', '.join(uses) or 'nowhere'}")

    check_error_keys(code, strings, report)
    check_tr(code, strings, report)
    check_icu(strings, report)
    return results


#----------------------------------------------------------------------------------------
def check_error_keys(code, strings, report):
    '''
    The message keys the Configure screens display (errors[...] = 'key', {'base': 'key'},
    self.header_msg = 'key', 'done_msg': 'key') must be options.error texts, HA and
    async_options_error_msgs display the raw key otherwise
    '''
    errors = strings.get('options', {}).get('error', {})
    for path, tree in code.modules.items():
        if not (path.startswith(f"{PKG}/configure/") or path.endswith('config_flow.py')):
            continue
        for node in ast.walk(tree):
            keys = []
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if (isinstance(t, ast.Subscript) and 'errors' in _src(t.value)
                            or _src(t) == 'self.header_msg'):
                        keys.append(node.value)
            if isinstance(node, ast.Dict):
                for k, v in zip(node.keys, node.values):
                    if k is not None and _const_str(k, code.consts) in ('base', 'done_msg'):
                        keys.append(v)
            for v in keys:
                for cand in ([v.body, v.orelse] if isinstance(v, ast.IfExp) else [v]):
                    key = _const_str(cand, code.consts)
                    if key and key not in errors:
                        report('ERROR', f"options.error.{key} is displayed but not in strings.json, "
                                        f"the raw key is displayed  [{path.replace(PKG + '/', '')}:{node.lineno}]")


def check_tr(code, strings, report):
    '''utils_cf.tr / tr_cnt / tr_path keyword placeholders'''
    cf = strings.get('selector', {}).get('cf_text', {}).get('options', {})
    def lookup(path):
        node = strings
        for part in path.split('.'):
            if not isinstance(node, dict) or part not in node:
                return None
            node = node[part]
        return node if isinstance(node, str) else None

    for path, tree in code.modules.items():
        for call in ast.walk(tree):
            if not isinstance(call, ast.Call) or _call_name(call) not in ('tr', 'tr_cnt', 'tr_path'):
                continue
            if not call.args:
                continue
            name = _call_name(call)
            given = {kw.arg for kw in call.keywords if kw.arg}
            star = any(kw.arg is None for kw in call.keywords)
            if name == 'tr_cnt':
                given.add('cnt')
            arg = call.args[0]
            where = f"{path.replace(PKG + '/', '')}:{call.lineno}"
            texts, fstring = {}, False
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                k = arg.value
                if name == 'tr_path':
                    texts[k] = lookup(k)
                elif name == 'tr_cnt':
                    texts.update({f"{k}_one": cf.get(f"{k}_one"), f"{k}_other": cf.get(f"{k}_other")})
                else:
                    texts[k] = cf.get(k)
            elif (isinstance(arg, ast.JoinedStr) and name == 'tr' and arg.values
                    and isinstance(arg.values[0], ast.Constant)):
                fstring = True
                pat = _fstring_pattern(arg)
                texts = {k: v for k, v in cf.items() if re.fullmatch(pat, k)}
                if not texts:
                    report('ERROR', f"tr({_src(arg)}) matches no selector.cf_text key  [{where}]")
            else:
                continue
            for k, text in texts.items():
                if text is None:
                    where_key = k if name == 'tr_path' else f"selector.cf_text.options.{k}"
                    if code.funcs.get(name):
                        report('ERROR', f"{name}({k!r}): {where_key} not in strings.json, "
                                        f"the raw key is displayed  [{where}]")
                    continue
                missing = set(PH_RE.findall(text)) - given
                if missing and not star:
                    report('WARN' if fstring else 'ERROR',
                           f"{name}: {k} uses {sorted(missing)}, not passed  [{where}]"
                           f"{' (f-string key, is it one of its values?)' if fstring else ''}")
                elif missing:
                    report('INFO', f"{name}: {k} uses {sorted(missing)}, passed with ** ?  [{where}]")


def check_icu(strings, report):
    '''Texts formatjs can't parse: { } around something other than a name, quoted braces'''
    def walk(node, path):
        if isinstance(node, dict):
            for k, v in node.items():
                if not k.startswith('_comment'):
                    walk(v, f"{path}.{k}" if path else k)
        elif isinstance(node, str):
            if path.startswith('selector.cf_text.') or path.startswith('services.'):
                return
            depth, buf = 0, ''
            for ch in node:
                if ch == '{':
                    depth += 1; buf = ''
                elif ch == '}':
                    depth -= 1
                    if depth == 0 and not re.fullmatch(r'\w+', buf):
                        report('ERROR', f"{path}: '{{{buf}}}' is not a placeholder, formatjs fails")
                    if depth < 0:
                        report('ERROR', f"{path}: unbalanced '}}'"); depth = 0
                elif depth:
                    buf += ch
            if depth:
                report('ERROR', f"{path}: unbalanced '{{'")
            if re.search(r"'[{}]", node):
                report('WARN', f"{path}: a ' before {{ or }} quotes it, the placeholder is shown as text")
    walk(strings, '')


#----------------------------------------------------------------------------------------
# Findings checked by hand that the script can't follow: (regex, reason). They are listed
# as INFO with -v. Some are for code that only exists with the Configure menus of #603.
ALLOW = [
    (r"options\.step\.menu\.description \['status_line'\] only passed on some branches",
     "status_line is added when menu_id == MAIN_MENU, the 'menu' step is the main menu"),
    (r"issues\.switch_repository\..* uses \['store'\]",
     "marketplace.py passes translation_placeholders={'store': ...} to post_config_error"),
    (r"tr: confirm_yes_delete_device uses \['device'\].*step_tools\.py",
     "confirm_yes_{tool_item}: tool_item is one of TOOL_CONFIRM_ITEMS, delete_device is not one"),
    (r"step\.reauth_hwkey_progress\.description: a ' before",
     "no async_show_form/async_show_progress shows the reauth_hwkey_progress step"),
    (r"tr: confirm_title_delete_device uses \['device'\].*step_tools\.py",
     "confirm_title_{tool_item}: tool_item is one of TOOL_CONFIRM_ITEMS, delete_device is not one"),
]

def allowed(results):
    out = []
    for level, msg in results:
        reason = next((r for pat, r in ALLOW if re.search(pat, msg)), None)
        if reason and level in ('WARN', 'ERROR'):
            out.append(('INFO', f"allowed ({reason}): {msg}"))
        else:
            out.append((level, msg))
    return out


def check(code, r, verbose=False):
    order = {'ERROR': 0, 'WARN': 1, 'INFO': 2}
    for level, msg in sorted(dict.fromkeys(allowed(check_all(code, verbose))), key=lambda x: order[x[0]]):
        if level != 'INFO' or verbose:
            r.add(level, msg)
