'''strings.json and the translations/*.json files'''
import json
import re

from .common import flatten

PH_RE = re.compile(r'\{(\w+)\}')


def check(code, r):
    try:
        strings = code.strings
    except (OSError, ValueError) as err:
        r.error(f"strings.json: {err}")
        return
    langs = {}
    for path in code.translation_files():
        try:
            langs[path.stem] = json.loads(path.read_text(encoding='utf-8'))
        except ValueError as err:
            r.error(f"translations/{path.name} is not valid JSON: {err}")
    if 'en' not in langs:
        r.error('translations/en.json is missing')
        return

    # HA shows translations/en.json, strings.json is the source it is made from
    fs, fe = flatten(strings), flatten(langs['en'])
    for key in sorted(set(fs) | set(fe)):
        if key not in fe:
            r.error(f"{key} is in strings.json, not in translations/en.json")
        elif key not in fs:
            r.error(f"{key} is in translations/en.json, not in strings.json")
        elif fs[key] != fe[key]:
            r.error(f"{key} has another text in strings.json than in translations/en.json")

    # Other languages: a key en.json doesn't have is never shown, a placeholder the English
    # text doesn't have gets no value
    for lang, data in sorted(langs.items()):
        if lang == 'en':
            continue
        fl = flatten(data)
        stale = sorted(k for k in fl if k not in fe)
        if stale:
            r.warn(f"translations/{lang}.json has {len(stale)} keys that en.json doesn't have "
                   f"(never shown), e.g. {stale[:3]}")
        for key, text in sorted(fl.items()):
            if key in fe and isinstance(text, str) and isinstance(fe[key], str):
                extra = set(PH_RE.findall(text)) - set(PH_RE.findall(fe[key]))
                if extra:
                    r.error(f"translations/{lang}.json {key} uses {sorted(extra)}, "
                            f"the English text doesn't (no value is passed)")
