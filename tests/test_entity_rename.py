"""Contracts for the device-registry rename notice and the requirement pins.

``custom_components/icloud3/utils/entity_reg_util.py`` imports Home Assistant, so
these checks read the source instead of importing the module.

Two things must not regress silently:

* A device renamed in HA must be reported, not acted on. iCloud3 does not rewrite
  the configuration on its own; renaming the entities would break the user's
  automations that reference them by entity_id. Submit on the issue is the only
  path that copies the HA name into the configuration.
* The notice must be posted once per device, not on every registry update.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components/icloud3"
RENAME_MODULE = COMPONENT / "utils" / "entity_reg_util.py"
APPLE_MODULE = COMPONENT / "startup" / "start_ic3_apple.py"
HANDLER_NAME = "async_handle_update_device_registry"
RENAME_FUNCTION_NAME = "_report_device_rename"
RENAME_SET_NAME = "_rename_repair_devicenames"
CONFIG_WRITE_NAME = "write_icloud3_configuration_file"
FIX_ACTION_NAME = "update_ic3_device_name"
APPLY_FIX_NAME = "_fix_repair_issue_update_ic3_device_name"


def source_of(path: Path) -> str:
    return path.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def rename_tree() -> ast.Module:
    return ast.parse(source_of(RENAME_MODULE))


@pytest.fixture(scope="module")
def apple_tree() -> ast.Module:
    return ast.parse(source_of(APPLE_MODULE))


def registered_fix_actions(tree: ast.Module) -> dict[str, str]:
    actions: dict[str, str] = {}
    for node in tree.body:
        if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
            continue
        call = node.value
        if not (isinstance(call.func, ast.Name)
                and call.func.id == "register_repair_fix_handler"):
            continue
        action, handler = call.args
        actions[ast.literal_eval(action)] = handler.id
    return actions


@pytest.fixture(scope="module")
def fix_actions(apple_tree: ast.Module) -> dict[str, str]:
    return registered_fix_actions(apple_tree)


def function_node(tree: ast.Module, name: str) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    raise AssertionError(f"{name} not found")


def called_names(node: ast.AST) -> set[str]:
    names: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            func = child.func
            if isinstance(func, ast.Name):
                names.add(func.id)
            elif isinstance(func, ast.Attribute):
                names.add(func.attr)
    return names


def test_rename_is_checked_from_the_name_changes(rename_tree: ast.Module) -> None:
    node = function_node(rename_tree, RENAME_FUNCTION_NAME)
    body = ast.unparse(node)
    assert "'name' not in changes" in body
    assert "'name_by_user' not in changes" in body
    assert "device_data.name_by_user or device_data.name" in body
    assert "Device.fname" in body


def test_rename_is_reported_through_repairs(rename_tree: ast.Module) -> None:
    node = function_node(rename_tree, RENAME_FUNCTION_NAME)
    names = called_names(node)
    assert "post_repair_issue" in names
    assert "clear_repair_issue" in names

    source = ast.unparse(node)
    assert "device_renamed_{devicename}" in source
    assert "severity='warning'" in source
    assert "fix_action='update_ic3_device_name'" in source
    assert "'devicename': devicename" in source
    assert "'new_name': new_name" in source


def test_rename_issue_is_fixed_by_submit(apple_tree: ast.Module, rename_tree: ast.Module,
                                         fix_actions: dict[str, str]) -> None:
    assert fix_actions[FIX_ACTION_NAME] == APPLY_FIX_NAME

    handler = ast.unparse(function_node(apple_tree, APPLY_FIX_NAME))
    assert "(fix_data.get('new_name') or '').strip()" in handler
    assert "conf_device[CONF_FNAME] = new_name" in handler
    assert "config_file.write_icloud3_configuration_file()" in handler
    assert "Gb.was_icloud3_restart_requested = True" in handler
    assert "return False" in handler
    assert "return True" in handler

    # The rename path only reports; the configuration is written by the handler
    # after Submit.
    rename_source = ast.unparse(function_node(rename_tree, RENAME_FUNCTION_NAME))
    assert "write_icloud3_configuration_file" not in rename_source


def test_rename_issue_is_posted_once_per_device(rename_tree: ast.Module) -> None:
    module_level = {
        target.id
        for stmt in rename_tree.body
        if isinstance(stmt, ast.Assign)
        for target in stmt.targets
        if isinstance(target, ast.Name)
    }
    assert RENAME_SET_NAME in module_level

    assignment = next(
        stmt
        for stmt in rename_tree.body
        if isinstance(stmt, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == RENAME_SET_NAME for t in stmt.targets)
    )
    assert isinstance(assignment.value, ast.Call)
    assert isinstance(assignment.value.func, ast.Name)
    assert assignment.value.func.id == "set"

    body = ast.unparse(function_node(rename_tree, RENAME_FUNCTION_NAME))
    assert f"if devicename in {RENAME_SET_NAME}:" in body
    assert f"{RENAME_SET_NAME}.add(devicename)" in body
    assert f"{RENAME_SET_NAME}.discard(devicename)" in body


def test_rename_path_does_not_write_the_configuration(rename_tree: ast.Module) -> None:
    for name in (RENAME_FUNCTION_NAME, HANDLER_NAME):
        names = called_names(function_node(rename_tree, name))
        assert not [
            called for called in names if CONFIG_WRITE_NAME in called
        ], f"{name} must not write the iCloud3 configuration"


def test_disabled_by_path_still_runs_first(rename_tree: ast.Module) -> None:
    body = ast.unparse(function_node(rename_tree, HANDLER_NAME))
    assert "if 'disabled_by' not in changes:" in body
    assert "if disabled_by is None:" in body
    assert "dr.DeviceEntryDisabler.USER" in body

    disabled_at = body.index("if 'disabled_by' not in changes:")
    rename_at = body.index(f"_report_device_rename(Device, devicename, device_data, changes)")
    assert disabled_at < rename_at


def test_rename_notice_text_points_at_the_configure_flow(rename_tree: ast.Module) -> None:
    body = ast.unparse(function_node(rename_tree, RENAME_FUNCTION_NAME))
    assert "Configure > Update iCloud3 Device" in body


def test_manifest_pins_tested_versions() -> None:
    manifest = json.loads(source_of(COMPONENT / "manifest.json"))

    assert manifest["requirements"] == [
        "srp>=1.0.22",
        "fido2>=2.2.1",
        "curl_cffi>=0.16.3",
    ]
    assert manifest["domain"] == "icloud3"
    assert manifest["dependencies"] == []
    assert manifest["config_flow"] is True
