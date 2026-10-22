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
