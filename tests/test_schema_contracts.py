"""Schema-version contracts for the configuration file and the config entry.

The integration imports Home Assistant, so the constants and the pure version
helper are read with `ast` instead of importing the package. The source checks
guard the downgrade protection and the backup rotation order; the
`is_supported_schema` test executes the real function body.
"""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components/icloud3"

CONFIG_FILE = "startup/config_file.py"


def _source(relative_path: str) -> str:
    return (COMPONENT / relative_path).read_text(encoding="utf-8")


def _module_constants(names: set[str]) -> dict[str, object]:
    tree = ast.parse(_source("const.py"))
    values: dict[str, object] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in names:
                values[target.id] = ast.literal_eval(node.value)
    return values


def _function_source(relative_path: str, function_name: str) -> str:
    source = _source(relative_path)
    tree = ast.parse(source)
    node = next(
        node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == function_name)
    segment = ast.get_source_segment(source, node)
    assert segment is not None
    return segment


def test_const_defines_the_config_schema_version() -> None:
    values = _module_constants({"CONFIG_SCHEMA_VERSION", "CONFIG_SCHEMA_VERSION_KEY"})
    assert values["CONFIG_SCHEMA_VERSION"] == 2
    assert values["CONFIG_SCHEMA_VERSION_KEY"] == "schema_version"


def test_default_profile_keeps_the_schema_key() -> None:
    tree = ast.parse(_source("const.py"))
    node = next(
        node for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "DEFAULT_PROFILE_CONF"
                for target in node.targets))
    assert isinstance(node.value, ast.Dict)
    keys = {ast.unparse(key) for key in node.value.keys}
    # Profile updates delete keys that are missing from DEFAULT_PROFILE_CONF.
    # Without this entry the migration stamp is stripped on every startup.
    assert "CONFIG_SCHEMA_VERSION_KEY" in keys


def test_is_supported_schema_accepts_supported_and_rejects_newer() -> None:
    namespace = {
        "CONFIG_SCHEMA_VERSION": _module_constants({"CONFIG_SCHEMA_VERSION"})[
            "CONFIG_SCHEMA_VERSION"],
    }
    exec(_function_source(CONFIG_FILE, "is_supported_schema"), namespace)
    is_supported_schema = namespace["is_supported_schema"]

    assert is_supported_schema(1) is True
    assert is_supported_schema(2) is True
    assert is_supported_schema("2") is True
    assert is_supported_schema(3) is False
    assert is_supported_schema(0) is False
    assert is_supported_schema(None) is False
    assert is_supported_schema("newer") is False


def test_missing_schema_version_is_read_as_one() -> None:
    function = _function_source(CONFIG_FILE, "_config_schema_version")
    assert ".get(CONFIG_SCHEMA_VERSION_KEY, 1)" in function

    namespace = {
        "Gb": SimpleNamespace(conf_profile={}),
        "CONFIG_SCHEMA_VERSION_KEY": "schema_version",
    }
    exec(function, namespace)
    schema_version = namespace["_config_schema_version"]

    assert schema_version() == 1
    namespace["Gb"].conf_profile = {"schema_version": 2}
    assert schema_version() == 2
    namespace["Gb"].conf_profile = {"schema_version": "newer"}
    assert schema_version() == 1
    namespace["Gb"].conf_profile = {"schema_version": 0}
    assert schema_version() == 1


def test_backup_rotation_order_is_newest_first() -> None:
    class FakeFileIO:
        deleted: list[str] = []
        renamed: list[tuple[str, str]] = []

        def delete_file(self, filename: str) -> None:
            self.deleted.append(filename)

        def rename_file(self, old_name: str, new_name: str) -> None:
            self.renamed.append((old_name, new_name))

    fake_file_io = FakeFileIO()
    namespace = {
        "Gb": SimpleNamespace(icloud3_config_filename="config"),
        "file_io": fake_file_io,
        "_CONFIG_BACKUP_ROTATION_COUNT": 5,
        "_LOGGER": SimpleNamespace(warning=lambda *_: None),
    }
    exec(_function_source(CONFIG_FILE, "_rotate_config_backup_files"), namespace)
    namespace["_rotate_config_backup_files"]()

    assert fake_file_io.deleted == ["config_backup_5"]
    assert fake_file_io.renamed == [
        ("config_backup_4", "config_backup_5"),
        ("config_backup_3", "config_backup_4"),
        ("config_backup_2", "config_backup_3"),
        ("config_backup_1", "config_backup_2"),
        ("config_backup", "config_backup_1"),
    ]


def test_read_calls_the_schema_migration() -> None:
    function = _function_source(CONFIG_FILE, "read_icloud3_configuration_file")
    assert "_migrate_config_schema()" in function


def test_downgrade_guard_returns_before_any_write() -> None:
    function = _function_source(CONFIG_FILE, "_migrate_config_schema")
    assert "is_supported_schema(schema_version)" in function
    assert "CONFIG_SCHEMA_VERSION_KEY" in function
    assert "log_error_msg" in function
    assert "post_alert" in function
    assert "return False" in function
    assert "return True" in function
    # Only the version is stamped; user settings keep their values.
    assert "CONF_UPDATE_DATE" not in function
    assert "_reconstruct_conf_file" not in function
    # Reading a backup must not write the live file; the version is only
    # stamped in memory and persisted by the next regular write.
    assert "file_io.save_json_file" not in function


def test_write_stamps_the_schema_before_saving() -> None:
    function = _function_source(CONFIG_FILE, "_write_icloud3_configuration_file")
    assert "CONFIG_SCHEMA_VERSION_KEY" in function
    assert function.index("CONFIG_SCHEMA_VERSION_KEY") < function.index(
        "file_io.save_json_file")


def test_backup_rotation_keeps_five_newest_files() -> None:
    function = _function_source(CONFIG_FILE, "_rotate_config_backup_files")
    assert "_CONFIG_BACKUP_ROTATION_COUNT" in function
    # Shift 4->5, 3->4, ... before the live _backup becomes _backup_1.
    assert "range(_CONFIG_BACKUP_ROTATION_COUNT - 1, 0, -1)" in function
    assert "f\"{Gb.icloud3_config_filename}_backup_{index}\"" in function
    assert "f\"{Gb.icloud3_config_filename}_backup_{index + 1}\"" in function
    assert 'f"{Gb.icloud3_config_filename}_backup_1"' in function


def test_backup_rotates_before_the_backup_is_overwritten() -> None:
    function = _function_source(CONFIG_FILE, "_write_icloud3_configuration_file")
    assert "filename_suffix == '_backup'" in function
    assert function.index("_rotate_config_backup_files()") < function.index(
        "file_io.save_json_file")


def test_restore_tries_the_rotated_backups() -> None:
    function = _function_source(CONFIG_FILE, "_restore_config_file_from_backup")
    assert "_CONFIG_BACKUP_ROTATION_COUNT" in function
    assert "_backup_1" not in function  # built from the count, not hard-coded
    assert "read_icloud3_configuration_file(filename_suffix)" in function


def test_config_repair_issue_ids_are_stable() -> None:
    tree = ast.parse(_source(CONFIG_FILE))
    values = {
        target.id: node.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    assert ast.literal_eval(values["CONFIG_WRITE_FAILED_ISSUE_ID"]) == "config_write_failed"
    assert ast.literal_eval(values["CONFIG_SCHEMA_NEWER_ISSUE_ID"]) == "config_schema_newer"
    assert ast.literal_eval(values["CONFIG_REPAIR_ALERT_KEY"]) == "config"


def test_config_repair_issues_are_guarded_and_informational() -> None:
    function = _function_source(CONFIG_FILE, "_post_config_repair_issue")
    assert "if Gb.hass is None:" in function
    assert "post_repair_issue(" in function
    assert "alert_key" in function and "CONFIG_REPAIR_ALERT_KEY" in function
    # A configuration problem can only be acknowledged; Submit must not hide it.
    assert "fix_action = None" in function
    assert "_LOGGER.exception(err)" in function


def test_write_failure_posts_an_error_issue() -> None:
    function = _function_source(CONFIG_FILE, "_post_config_write_failed_issue")
    assert "CONFIG_WRITE_FAILED_ISSUE_ID" in function
    assert "'iCloud3 configuration could not be saved'" in function
    assert "'error'" in function


def test_schema_newer_posts_a_warning_issue() -> None:
    function = _function_source(CONFIG_FILE, "_post_config_schema_newer_issue")
    assert "CONFIG_SCHEMA_NEWER_ISSUE_ID" in function
    assert "'iCloud3 configuration is newer than this version'" in function
    assert "'warning'" in function


def test_write_posts_on_failure_and_clears_on_success() -> None:
    function = _function_source(CONFIG_FILE, "_write_icloud3_configuration_file")
    assert "_post_config_write_failed_issue(" in function
    assert "_clear_config_write_failed_issue()" in function
    assert function.index("_post_config_write_failed_issue(") > function.index(
        "file_io.save_json_file")
    assert function.index("_clear_config_write_failed_issue()") > function.index(
        "if success is False:")


def test_migrate_posts_and_clears_the_newer_schema_issue() -> None:
    function = _function_source(CONFIG_FILE, "_migrate_config_schema")
    assert "_post_config_schema_newer_issue(log_msg)" in function
    assert "_clear_config_schema_newer_issue()" in function
    assert function.index("_post_config_schema_newer_issue(log_msg)") < function.index(
        "_clear_config_schema_newer_issue()")


def test_init_defines_async_migrate_entry() -> None:
    source = _source("__init__.py")
    assert "async def async_migrate_entry" in source

    function = _function_source("__init__.py", "async_migrate_entry")
    assert "from .config_flow import iCloud3_ConfigFlow" in function
    assert "iCloud3_ConfigFlow.VERSION" in function
    assert "entry.version" in function
    assert "entry.minor_version" in function
    assert "return False" in function
    assert "return True" in function
