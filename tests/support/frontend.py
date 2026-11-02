'''
Render an options/config/repair flow result like the HA frontend (20260930.x) does, from the
serialized result (what the REST API sends) and the integration's translations, and report
what would look broken in the browser.

What the frontend passes to localize() (see checks/placeholders.py):
    form   title, description, data, data_description, sections.*  - step placeholders
    menu   title                                                    - NO placeholders
           description, menu_options (list), menu_option_descriptions - step placeholders
           {option: label} menu_options                             - the label as is
    error  <flow>.error.<key>                                       - the form's placeholders
    abort  <flow>.abort.<reason>                                    - the abort placeholders
A placeholder without a value makes formatjs throw and the frontend shows
'Translation [formatjs Error: MISSING_VALUE] ...'. A missing field label shows the raw field
name, a missing selector option label shows the option value.
'''
from __future__ import annotations

import re
import unicodedata

MISSING = 'Translation [formatjs Error: MISSING_VALUE]'
RAW_KEY_RE = re.compile(r'\b(component\.icloud3|selector\.cf_text|options\.step|options\.error|'
                        r'config\.step|cf_text\.options)\b')
LEFTOVER_PH_RE = re.compile(r'\{\s*\w+\s*\}')
SNAKE_RE = re.compile(r'(?<![\w./:-])([a-z][a-z0-9]*(?:_[a-z0-9]+)+)(?![\w./:-])')


class ICUError(ValueError):
    pass


#----------------------------------------------------------------------------------------
#   Minimal ICU MessageFormat (intl-messageformat semantics for what HA strings use)
#----------------------------------------------------------------------------------------
def icu_format(text, values, strict=True):
    '''Returns (formatted, missing_args). Raises ICUError on a syntax error'''
    out, missing = _Parser(text, values).parse()
    return out, missing


class _Parser:
    def __init__(self, text, values):
        self.s, self.i, self.values, self.missing = text, 0, values or {}, []

    def parse(self):
        out = self._message(top=True)
        if self.i < len(self.s):
            raise ICUError(f"unexpected '}}' at {self.i}")
        return out, self.missing

    def _message(self, top=False, plural_value=None):
        out = []
        s = self.s
        while self.i < len(s):
            c = s[self.i]
            if c == "'":
                # '' -> ', '{...}' quoted literal (only when it starts a syntax char)
                if self.i + 1 < len(s) and s[self.i + 1] == "'":
                    out.append("'"); self.i += 2; continue
                if self.i + 1 < len(s) and s[self.i + 1] in '{}#|' :
                    end = s.find("'", self.i + 1)
                    if end == -1:
                        out.append(s[self.i + 1:]); self.i = len(s); continue
                    out.append(s[self.i + 1:end]); self.i = end + 1; continue
                out.append(c); self.i += 1; continue
            if c == '{':
                out.append(self._argument()); continue
            if c == '}':
                if top:
                    raise ICUError(f"unbalanced '}}' at {self.i}")
                return ''.join(out)
            if c == '#' and plural_value is not None:
                out.append(str(plural_value)); self.i += 1; continue
            out.append(c); self.i += 1
        if not top:
            raise ICUError('unclosed {')
        return ''.join(out)

    def _argument(self):
        s = self.s
        self.i += 1
        m = re.compile(r'\s*([^\s,{}]*)\s*').match(s, self.i)
        name = m.group(1); self.i = m.end()
        if not name or not re.fullmatch(r'\w+', name):
            raise ICUError(f"bad argument name {name!r} at {self.i}")
        if self.i >= len(s):
            raise ICUError('unclosed {')
        if s[self.i] == '}':
            self.i += 1
            if name not in self.values:
                self.missing.append(name)
                return f"{{{name}}}"
            return str(self.values[name])
        if s[self.i] != ',':
            raise ICUError(f"expected , or }} after {name} at {self.i}")
        self.i += 1
        m = re.compile(r'\s*(\w+)\s*').match(s, self.i)
        kind = m.group(1); self.i = m.end()
        if kind in ('number', 'date', 'time'):
            end = s.find('}', self.i)
            if end == -1:
                raise ICUError('unclosed {')
            self.i = end + 1
            if name not in self.values:
                self.missing.append(name)
            return str(self.values.get(name, ''))
        if kind not in ('plural', 'select', 'selectordinal'):
            raise ICUError(f"unknown argument type {kind!r}")
        if s[self.i:self.i + 1] != ',':
            raise ICUError(f"expected , after {kind}")
        self.i += 1
        options = {}
        offset = 0
        while True:
            m = re.compile(r'\s*').match(s, self.i); self.i = m.end()
            if self.i >= len(s):
                raise ICUError('unclosed plural/select')
            if s[self.i] == '}':
                self.i += 1
                break
            m = re.compile(r'(offset:\d+|=?\w+)\s*').match(s, self.i)
            if not m:
                raise ICUError(f"bad selector at {self.i}")
            key = m.group(1); self.i = m.end()
            if key.startswith('offset:'):
                offset = int(key[7:]); continue
            if s[self.i:self.i + 1] != '{':
                raise ICUError(f"expected {{ after {key}")
            self.i += 1
            value = self.values.get(name)
            options[key] = self._message(plural_value=(value - offset if isinstance(value, (int, float)) else value)
                                         if kind != 'select' else None)
            self.i += 1
        if 'other' not in options:
            raise ICUError(f"{kind} without other")
        if name not in self.values:
            self.missing.append(name)
            return options['other']
        value = self.values[name]
        if kind == 'select':
            return options.get(str(value), options['other'])
        if f"={value}" in options:
            return options[f"={value}"]
        return options.get('one' if value == 1 else 'other', options['other'])


#----------------------------------------------------------------------------------------
class Rendered:
    def __init__(self, step, kind):
        self.step, self.kind = step, kind
        self.title = ''
        self.description = ''
        self.rows = []          # (key, label, description)
        self.fields = []        # (name, label, description, options[(value, label)])
        self.errors = []
        self.issues = []        # (level, where, message)
        self.code_labels = set()  # where of the option labels the code built (shown as is)

    def texts(self):
        yield 'title', self.title
        yield 'description', self.description
        for key, label, desc in self.rows:
            yield f"row {key}", label
            yield f"row {key} description", desc
        for name, label, desc, options in self.fields:
            yield f"field {name}", label
            yield f"field {name} description", desc
            for value, olabel in options:
                yield f"field {name} option {value}", olabel
        for key, text in self.errors:
            yield f"error {key}", text

    def text(self):
        return '\n'.join(t for _, t in self.texts() if t)


class VirtualFrontend:
    def __init__(self, translations, domain='icloud3', known_keys=()):
        '''translations: the flattened {component.icloud3....: text} dict of the language'''
        self.t, self.domain = translations, domain
        self.known_keys = set(known_keys)

    def _get(self, path):
        return self.t.get(f"component.{self.domain}.{path}")

    def _loc(self, r, where, path, values, required=False, fallback=''):
        text = self._get(path)
        if text is None:
            if required:
                r.issues.append(('ERROR', where, f"no translation {path} (shows {fallback!r})"))
            return fallback
        try:
            out, missing = icu_format(text, values)
        except ICUError as err:
            r.issues.append(('ERROR', where, f"formatjs syntax error in {path}: {err}"))
            return f"{MISSING} {text}"
        if missing:
            r.issues.append(('ERROR', where, f"{MISSING} {path}: no value for {missing}"))
            return f"{MISSING} {text}"
        return out

    def render(self, res, flow='options', issue_id=None):
        kind = res.get('type')
        step = res.get('step_id') or res.get('reason') or ''
        r = Rendered(step, kind)
        ph = res.get('description_placeholders') or {}
        base = (f"issues.{issue_id}.fix_flow" if flow == 'repair' else flow)
        sp = f"{base}.step.{step}"

        for key, value in ph.items():
            if value is None:
                r.issues.append(('WARN', f"placeholder {key}", 'value is None (shows "null")'))
            elif re.search(r'(^|[\s(:])None($|[\s),.])', str(value)):
                r.issues.append(('WARN', f"placeholder {key}", f"'None' shown: {str(value)[:80]!r}"))

        if kind == 'menu':
            r.title = self._loc(r, 'title', f"{sp}.title", {})
            r.description = self._loc(r, 'description', f"{sp}.description", ph)
            options = res.get('menu_options')
            if isinstance(options, dict):
                for key, label in options.items():
                    r.rows.append((key, label, ''))
                    r.code_labels.add(f"row {key}")
            else:
                for key in options or []:
                    label = self._loc(r, f"row {key}", f"{sp}.menu_options.{key}", ph,
                                      required=True, fallback=key)
                    desc = self._loc(r, f"row {key} description",
                                     f"{sp}.menu_option_descriptions.{key}", ph)
                    r.rows.append((key, label, desc))
        elif kind == 'form':
            r.title = self._loc(r, 'title', f"{sp}.title", ph)
            r.description = self._loc(r, 'description', f"{sp}.description", ph)
            self._fields(r, res.get('data_schema') or [], f"{sp}", ph)
            for field, key in (res.get('errors') or {}).items():
                if not key:
                    continue        # ha-form shows no error for a falsy value
                r.errors.append((field, self._loc(r, f"error {field}", f"{base}.error.{key}", ph,
                                                  required=True, fallback=key)))
        elif kind == 'abort':
            r.title = ''
            r.description = self._loc(r, 'abort', f"{base}.abort.{res.get('reason')}", ph,
                                      required=True, fallback=res.get('reason', ''))
        elif kind == 'progress':
            r.title = self._loc(r, 'title', f"{sp}.title", ph)
            r.description = self._loc(r, 'progress', f"{base}.progress.{res.get('progress_action')}", ph)
        self._text_checks(r, res)
        return r

    def _fields(self, r, schema, sp, ph, section=None):
        for fld in schema:
            name = fld.get('name')
            if fld.get('type') == 'expandable':
                sec = f"{sp}.sections.{name}"
                label = self._loc(r, f"section {name}", f"{sec}.name", ph, required=True, fallback=name)
                desc = self._loc(r, f"section {name} description", f"{sec}.description", ph)
                r.fields.append((name, label, desc, []))
                self._fields(r, fld.get('schema') or [], sp, ph, section=name)
                continue
            dpath = f"{sp}.sections.{section}" if section else sp
            label = self._loc(r, f"field {name}", f"{dpath}.data.{name}", ph, required=True, fallback=name)
            desc = self._loc(r, f"field {name} description", f"{dpath}.data_description.{name}", ph)
            options = []
            sel = (fld.get('selector') or {})
            select = sel.get('select')
            if select is not None:
                tkey = select.get('translation_key')
                for opt in select.get('options') or []:
                    if isinstance(opt, dict):
                        value, olabel = opt.get('value'), opt.get('label')
                    else:
                        value, olabel = opt, None
                    tl = None
                    if tkey:
                        tl = self._get(f"selector.{tkey}.options.{value}")
                        if tl is not None:
                            olabel = tl
                        elif olabel is None:
                            r.issues.append(('ERROR', f"field {name} option {value}",
                                f"no translation selector.{tkey}.options.{value} (shows the value)"))
                            olabel = str(value)
                    if olabel is None:
                        olabel = str(value)
                    if tl is None:
                        r.code_labels.add(f"field {name} option {value}")
                    if str(olabel).strip() == '':
                        r.issues.append(('ERROR', f"field {name} option {value}", 'empty option label'))
                    options.append((value, str(olabel)))
            r.fields.append((name, label, desc, options))

    def _text_checks(self, r, res):
        if r.kind in ('menu', 'form') and not r.title.strip():
            r.issues.append(('WARN', 'title', 'empty title'))
        # Placeholder values are shown as is (the user's own input may contain {x} or 'undefined')
        values = sorted((str(v) for v in (res.get('description_placeholders') or {}).values()
                         if v is not None and len(str(v)) > 1), key=len, reverse=True)
        for where, full_text in r.texts():
            if not full_text:
                if where.startswith(('row ', 'field ')) and not where.endswith('description'):
                    r.issues.append(('ERROR', where, 'empty label'))
                continue
            text = full_text
            for v in values:
                text = text.replace(v, '\u2039ph\u203a')
            if RAW_KEY_RE.search(text):
                r.issues.append(('ERROR', where, f"raw translation key: {RAW_KEY_RE.search(text).group()!r} in {text[:80]!r}"))
            # An option label the code built is not formatted by the frontend, a '{x}' in
            # it is the user's own text (a device or account name)
            if MISSING not in text and LEFTOVER_PH_RE.search(text) and where not in r.code_labels:
                r.issues.append(('ERROR', where, f"unfilled placeholder {LEFTOVER_PH_RE.search(text).group()} in {text[:80]!r}"))
            for bad in ('[object Object]', 'undefined', 'NaN', '[%key:'):
                if bad in text:
                    r.issues.append(('ERROR', where, f"{bad!r} in {text[:80]!r}"))
            for m in SNAKE_RE.finditer(text):
                if m.group(1) in self.known_keys:
                    r.issues.append(('WARN', where, f"looks like a raw key {m.group(1)!r} in {text[:80]!r}"))
                    break
            for ch in set(full_text):
                cat = unicodedata.category(ch)
                if cat in ('Co', 'Cn', 'Cs') or ch in '\ufffd\u25a1':
                    r.issues.append(('ERROR', where, f"unrenderable char U+{ord(ch):04X} in {full_text[:60]!r}"))

def flatten(d, prefix=''):
    out = {}
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            out.update(flatten(v, key))
        else:
            out[key] = v
    return out


def collect_keys(strings):
    '''Snake case keys and option ids of strings.json (to spot raw keys in the texts)'''
    keys = set()
    def walk(d):
        for k, v in d.items():
            if '_' in k:
                keys.add(k)
            if isinstance(v, dict):
                walk(v)
    walk(strings)
    return keys
