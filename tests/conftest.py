"""Load Home Assistant free helper modules without importing the integration.

``custom_components/icloud3/__init__.py`` imports Home Assistant, so a normal
package import would require a full HA test harness. The helpers under test are
deliberately self-contained and are loaded by path instead.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, relative_path: str) -> ModuleType:
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def mobapp_resolver() -> ModuleType:
    return load_module(
        "icloud3_mobapp_resolver",
        "custom_components/icloud3/startup/mobapp_resolver.py",
    )


@pytest.fixture(scope="session")
def backoff() -> ModuleType:
    return load_module(
        "icloud3_backoff",
        "custom_components/icloud3/utils/backoff.py",
    )


@pytest.fixture(scope="session")
def pure() -> ModuleType:
    return load_module(
        "icloud3_pure",
        "custom_components/icloud3/utils/pure.py",
    )


@pytest.fixture(scope="session")
def diagnostics_module() -> ModuleType:
    """Load diagnostics.py with a minimal package shim.

    diagnostics.py uses relative imports for const/global_variables, but the
    real package __init__ imports Home Assistant. Registering the package path
    lets the submodules load without executing the integration __init__.
    """
    import types

    for name, path in (
        ("custom_components", ROOT / "custom_components"),
        ("custom_components.icloud3", ROOT / "custom_components/icloud3"),
    ):
        if name not in sys.modules:
            package = types.ModuleType(name)
            package.__path__ = [str(path)]  # type: ignore[attr-defined]
            sys.modules[name] = package

    # const.py needs two constants from homeassistant.const at import time.
    if "homeassistant" not in sys.modules:
        ha = types.ModuleType("homeassistant")
        ha.__path__ = []  # type: ignore[attr-defined]
        sys.modules["homeassistant"] = ha
    if "homeassistant.const" not in sys.modules:
        ha_const = types.ModuleType("homeassistant.const")
        ha_const.STATE_HOME = "home"
        ha_const.STATE_NOT_HOME = "not_home"
        sys.modules["homeassistant.const"] = ha_const

    load_module(
        "custom_components.icloud3.const",
        "custom_components/icloud3/const.py",
    )
    load_module(
        "custom_components.icloud3.global_variables",
        "custom_components/icloud3/global_variables.py",
    )
    return load_module(
        "custom_components.icloud3.diagnostics",
        "custom_components/icloud3/diagnostics.py",
    )
