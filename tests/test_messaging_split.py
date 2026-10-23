"""Contracts for the iCloud3 log file helpers moved from utils/messaging.py.

messaging.py imports Home Assistant, so the split is checked at source level:
each helper must be defined exactly once (in utils/log_file.py) and the
existing callers must keep working through messaging's re-export. The
re-export identity check runs in place and skips when Home Assistant is absent.
"""

from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
UTILS = ROOT / "custom_components/icloud3/utils"

MOVED_FUNCTIONS = (
    'open_ic3log_file',
    'close_ic3log_file',
    'write_ic3log_recd',
    'check_ic3log_file_exists',
    'archive_ic3log_file',
    'write_config_file_to_ic3log',
)


def source_of(path: Path) -> str:
    return path.read_text(encoding='utf-8')


def module_level_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            names.update(t.id for t in node.targets if isinstance(t, ast.Name))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
    return names


def module_level_imports(tree: ast.Module) -> list[tuple[str, set[str]]]:
    """Return (module, imported names) for imports executed at import time."""
    found: list[tuple[str, set[str]]] = []
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            found.append((node.module or '', {alias.name for alias in node.names}))
        elif isinstance(node, ast.Import):
            found.append(('', {alias.name for alias in node.names}))
    return found


def lazy_messaging_imports(tree: ast.Module) -> set[str]:
    return {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and (node.module or '').endswith('messaging')
        for alias in node.names
    }


def test_functions_are_defined_in_log_file() -> None:
    tree = ast.parse(source_of(UTILS / 'log_file.py'))
    defined = module_level_names(tree)
    missing = [name for name in MOVED_FUNCTIONS if name not in defined]
    assert missing == []


def test_functions_are_no_longer_defined_in_messaging() -> None:
    tree = ast.parse(source_of(UTILS / 'messaging.py'))
    defined = module_level_names(tree)
    still_defined = [name for name in MOVED_FUNCTIONS if name in defined]
    assert still_defined == []


def test_messaging_reexports_the_functions() -> None:
    tree = ast.parse(source_of(UTILS / 'messaging.py'))
    reexports = [
        names for module, names in module_level_imports(tree)
        if (module or '').endswith('log_file')
    ]
    assert reexports, "messaging must re-export the log file helpers from .log_file"
    assert set(MOVED_FUNCTIONS) <= set().union(*reexports)

    # A local definition would shadow the re-export and silently restore the
    # duplication this split removed.
    defined = module_level_names(tree)
    assert [name for name in MOVED_FUNCTIONS if name in defined] == []


def test_log_file_does_not_import_messaging_at_module_level() -> None:
    tree = ast.parse(source_of(UTILS / 'log_file.py'))
    module_level = module_level_imports(tree)
    assert [entry for entry in module_level if 'messaging' in entry[0]] == []
    assert [entry for entry in module_level
            if any('messaging' in name for name in entry[1])] == []


def test_log_file_imports_messaging_only_inside_functions() -> None:
    tree = ast.parse(source_of(UTILS / 'log_file.py'))
    lazy = lazy_messaging_imports(tree)
    # The helpers these functions call back into messaging for; importing them
    # at module level would close the messaging <-> log_file cycle.
    assert {'LoggerFilter', 'log_exception', 'log_exception_HA',
            'format_startup_header_box', 'post_event', 'log_info_msg'} <= lazy


def test_messaging_reexport_is_the_same_object() -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    try:
        messaging = importlib.import_module('custom_components.icloud3.utils.messaging')
    except ImportError as err:
        pytest.skip(f"Home Assistant is not installed: {err}")

    log_file = importlib.import_module('custom_components.icloud3.utils.log_file')
    for name in MOVED_FUNCTIONS:
        assert getattr(messaging, name) is getattr(log_file, name), name


