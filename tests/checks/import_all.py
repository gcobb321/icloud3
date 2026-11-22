'''
Import every iCloud3 module with Home Assistant (and the other packages HA provides)
replaced by stubs, so no Home Assistant install is needed. A module that fails to import
(a missing name in a from-import, a syntax error, a circular import the package order
doesn't resolve) is listed. Run by check_configure.py in its own process:

    python -B import_all.py DIR      DIR contains custom_components/icloud3
'''
import importlib
import importlib.abc
import importlib.machinery
import os
import sys
import traceback
import types
from unittest.mock import MagicMock

ROOT = sys.argv[1]
IC3 = f"{ROOT}/custom_components/icloud3"


class _Sel:
    def __init__(self, config=None, **kw):
        self.config = config if config is not None else kw
    def __call__(self, value):
        return value

class _SelCfg(dict):
    pass

selector_mod = types.ModuleType('homeassistant.helpers.selector')
for name in ['TextSelector', 'SelectSelector', 'BooleanSelector', 'NumberSelector', 'EntitySelector',
             'TimeSelector', 'IconSelector']:
    setattr(selector_mod, name, type(name, (_Sel,), {}))
for name in ['TextSelectorConfig', 'SelectSelectorConfig', 'NumberSelectorConfig', 'EntitySelectorConfig']:
    setattr(selector_mod, name, type(name, (_SelCfg,), {}))
selector_mod.__getattr__ = lambda name: type(name, (_Sel,), {})


class _StubMeta(type):
    def __getattr__(cls, name):
        if name.startswith('__'):
            raise AttributeError(name)
        return MagicMock(name=f"{cls.__name__}.{name}")


class _StubModule(types.ModuleType):
    def __getattr__(self, name):
        if name.startswith('__'):
            raise AttributeError(name)
        if name in ('MAJOR_VERSION', 'MINOR_VERSION'):
            value = {'MAJOR_VERSION': 2026, 'MINOR_VERSION': 10}[name]
        elif name.isupper():
            value = name.lower()
        elif name[:1].isupper():
            value = _StubMeta(name, (), {'__init__': lambda self, *a, **k: None,
                                    '__init_subclass__': classmethod(lambda cls, **kw: None)})
        else:
            value = MagicMock(name=f"{self.__name__}.{name}")
        setattr(self, name, value)
        return value


class _Finder(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    def find_spec(self, fullname, path, target=None):
        if fullname == 'homeassistant' or fullname.startswith('homeassistant.'):
            return importlib.machinery.ModuleSpec(fullname, self, is_package=True)
        return None
    def create_module(self, spec):
        if spec.name == 'homeassistant.helpers.selector':
            return selector_mod
        mod = _StubModule(spec.name)
        mod.__path__ = []
        return mod
    def exec_module(self, module):
        if module.__name__ == 'homeassistant.helpers':
            module.selector = selector_mod
        if module.__name__ == 'homeassistant.helpers.config_validation':
            module.boolean = bool
        if module.__name__ == 'homeassistant.data_entry_flow':
            module.section = lambda schema, opts: ('section', schema, opts)
        if module.__name__ == 'homeassistant.core':
            module.callback = lambda f: f

class _FallbackFinder(_Finder):
    '''Any other package that is not installed (requests, srp, fido2, ...)'''
    def find_spec(self, fullname, path, target=None):
        top = fullname.split('.')[0]
        if (fullname.startswith('custom_components') or top.startswith('_')
                or top in sys.stdlib_module_names):
            return None
        return importlib.machinery.ModuleSpec(fullname, self, is_package=True)

sys.meta_path.insert(0, _Finder())
sys.meta_path.append(_FallbackFinder())
sys.dont_write_bytecode = True

for pkg, path in [('custom_components', f"{ROOT}/custom_components"), ('custom_components.icloud3', IC3)]:
    mod = types.ModuleType(pkg)
    mod.__path__ = [path]
    sys.modules[pkg] = mod

# The package __init__ import order, it resolves the circular imports
FIRST = ['global_variables', 'const', 'const_config', 'const_char', 'utils.messaging',
         'utils.time_util', 'utils.file_io', 'utils.entity_reg_util', 'device_tracker', 'sensor',
         'apple_acct.internet_error', 'apple_acct.apple_acct_upw', 'icloud3_main',
         'startup.start_ic3', 'startup.config_file']
modules = []
for root, dirs, names in os.walk(IC3):
    dirs[:] = [d for d in dirs if d != '__pycache__']
    for n in sorted(names):
        if n.endswith('.py') and n != '__init__.py':
            rel = os.path.relpath(os.path.join(root, n), IC3)[:-3].replace(os.sep, '.')
            modules.append(rel)
order = [m for m in FIRST if m in modules] + sorted(m for m in modules if m not in FIRST)

failed = []
for m in order:
    try:
        importlib.import_module(f"custom_components.icloud3.{m}")
    except Exception as err:
        failed.append(m)
        print(f"FAIL {m}: {type(err).__name__}: {err}")
        traceback.print_exc(limit=-2, file=sys.stdout)

print(f"{len(order) - len(failed)}/{len(order)} modules imported")
sys.exit(1 if failed else 0)
