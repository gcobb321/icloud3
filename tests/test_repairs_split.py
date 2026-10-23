"""Contracts for the Repairs helpers moved from utils/messaging.py.

messaging.py imports Home Assistant, so the split is checked at the source
level: each helper must be defined exactly once (in repairs_util) and the
existing callers must keep working through messaging's re-export.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components/icloud3"
UTILS = COMPONENT / "utils"

MOVED_FUNCTIONS = (
    'post_repair_issue',
    'clear_repair_issue',
    'clear_repair_issues',
    'clear_repair_issue_alert_msg',
    'register_repair_fix_handler',
    '_evlog_msg_to_markdown',
    '_run_in_event_loop',
)

MOVED_NAMES = ('REPAIR_ISSUED_ALERT_MSG', 'repair_fix_handlers')

REEXPORTED = (
    'REPAIR_ISSUED_ALERT_MSG',
    'repair_fix_handlers',
    'post_repair_issue',
    'clear_repair_issue',
    'clear_repair_issues',
    'clear_repair_issue_alert_msg',
    'register_repair_fix_handler',
)

# _run_in_event_loop stays in messaging because entity_io/entity_reg_util import
# it from there; repairs_util has its own copy so it needs no messaging import.
NOT_IN_MESSAGING = tuple(
    name for name in MOVED_FUNCTIONS + MOVED_NAMES if name != '_run_in_event_loop')


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


def imports_from(tree: ast.Module, module_ends_with: str) -> tuple[str, set[str]] | None:
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom) or node.module is None:
            continue
        if node.module == module_ends_with or node.module.endswith(module_ends_with):
            return node.module, {alias.name for alias in node.names}
    return None


def test_helpers_are_defined_in_repairs_util() -> None:
    tree = ast.parse(source_of(UTILS / 'repairs_util.py'))
    defined = module_level_names(tree)
    missing = [name for name in MOVED_FUNCTIONS + MOVED_NAMES if name not in defined]
    assert missing == []


def test_helpers_are_no_longer_defined_in_messaging() -> None:
    tree = ast.parse(source_of(UTILS / 'messaging.py'))
    defined = module_level_names(tree)
    still_defined = [name for name in NOT_IN_MESSAGING if name in defined]
    assert still_defined == []


def test_messaging_reexports_the_helpers() -> None:
    tree = ast.parse(source_of(UTILS / 'messaging.py'))
    found = imports_from(tree, 'repairs_util')
    assert found is not None, "messaging must re-export from .repairs_util"
    module, names = found
    assert module == 'repairs_util'
    assert set(REEXPORTED) <= names

    # A local definition would shadow the re-export and silently restore the
    # duplicated helper this split removed.
    defined = module_level_names(tree)
    assert [name for name in REEXPORTED if name in defined] == []


def test_repairs_util_imports_messaging_only_lazily() -> None:
    tree = ast.parse(source_of(UTILS / 'repairs_util.py'))
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            module = getattr(node, 'module', None) or ''
            names = [alias.name for alias in node.names]
            assert 'messaging' not in module
            assert 'messaging' not in names

    # The messaging routines used at call time are imported in the functions
    # that call them, which keeps the module import acyclic.
    function_imports = [
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and (node.module or '').endswith('messaging')
        for alias in node.names
    ]
    assert 'update_alert_sensor' in function_imports
    assert 'log_exception' in function_imports


def test_ha_platform_module_uses_the_reexport() -> None:
    tree = ast.parse(source_of(COMPONENT / 'repairs.py'))
    found = imports_from(tree, 'utils.messaging')
    assert found is not None, "repairs.py must import through .utils.messaging"
    _, names = found
    assert {'repair_fix_handlers', 'clear_repair_issue_alert_msg'} <= names


def test_repairs_callers_keep_importing_from_messaging() -> None:
    callers = {
        'startup/start_ic3.py': {
            'post_repair_issue', 'clear_repair_issues', 'register_repair_fix_handler'},
        'apple_acct/apple_acct_support.py': {'post_repair_issue', 'clear_repair_issue'},
        'mobile_app/mobapp_data_handler.py': {'post_repair_issue', 'clear_repair_issue'},
    }
    for relative_path, expected in callers.items():
        tree = ast.parse(source_of(COMPONENT / relative_path))
        found = imports_from(tree, 'utils.messaging')
        assert found is not None, relative_path
        assert expected <= found[1], relative_path


def _load_repairs_util_without_home_assistant() -> dict[str, Any]:
    """Run the module's own statements, skipping the import statements.

    The helpers only touch Gb/hass when they are called, so the registry and the
    slug helpers are not needed to check which handlers are registered.
    """
    tree = ast.parse(source_of(UTILS / 'repairs_util.py'))
    tree.body = [node for node in tree.body
                 if not isinstance(node, (ast.Import, ast.ImportFrom))]
    namespace: dict[str, Any] = {}
    exec(compile(tree, 'repairs_util.py', 'exec'), namespace)
    return namespace


def test_acknowledge_handler_is_registered() -> None:
    namespace = _load_repairs_util_without_home_assistant()
    handler = namespace['repair_fix_handlers']['acknowledge']
    assert handler({'devicename': '', 'alert_key': 'x', 'fix_action': 'acknowledge'}) is True


def test_register_repair_fix_handler_registers_the_handler() -> None:
    namespace = _load_repairs_util_without_home_assistant()

    def handler(fix_data: dict[str, Any]) -> bool:
        return fix_data.get('fix_action') == 'test_action'

    namespace['register_repair_fix_handler']('test_action', handler)
    assert namespace['repair_fix_handlers']['test_action'] is handler
