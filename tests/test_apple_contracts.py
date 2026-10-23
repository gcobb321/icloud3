"""Contracts for the Apple Account auth modules.

The integration imports Home Assistant, so the modules under test are either
loaded by path (exceptions.py has no imports) or read as source with ``ast``.
Each check pins a bug that was fixed by hand: the dead raise in
``_raise_error``, the duplicated exception classes and the missing-field
tolerance in the device refresh loop.
"""

from __future__ import annotations

import ast
import importlib.util
from functools import lru_cache
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components/icloud3"


@lru_cache(maxsize=1)
def exceptions_module() -> ModuleType:
    path = COMPONENT / "apple_acct/exceptions.py"
    spec = importlib.util.spec_from_file_location("icloud3_apple_acct_exceptions", path)
    assert spec is not None and spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def source_of(relative_path: str) -> str:
    return (COMPONENT / relative_path).read_text(encoding="utf-8")


def tree_of(relative_path: str) -> ast.Module:
    return ast.parse(source_of(relative_path))


def function_named(tree: ast.Module, name: str) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node

    raise AssertionError(f"function {name} not found")


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#   exceptions.py - hierarchy and __init__ signatures
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def test_exceptions_module_imports_nothing() -> None:
    tree = tree_of("apple_acct/exceptions.py")
    imports = [node for node in ast.walk(tree)
               if isinstance(node, (ast.Import, ast.ImportFrom))]
    assert imports == []


def test_exception_hierarchy_is_unchanged() -> None:
    exc = exceptions_module()

    assert issubclass(exc.AppleAcctException, Exception)
    assert issubclass(exc.AppleAcctAPIResponseException, exc.AppleAcctException)
    assert issubclass(exc.AppleAcctManagerNotActivatedException,
                      exc.AppleAcctAPIResponseException)
    assert issubclass(exc.AppleAcctManagerNotActivatedException, exc.AppleAcctException)

    for name in ("AppleAcctFailedLoginException",
                 "AppleAcct2FARequiredException",
                 "AppleAcct2SARequiredException",
                 "AppleAcctNoStoredPasswordAvailableException",
                 "AppleAcctNoDevicesException"):
        exception_class = getattr(exc, name)
        assert issubclass(exception_class, exc.AppleAcctException), name


def test_api_response_exception_message_and_attributes() -> None:
    exc = exceptions_module()

    error = exc.AppleAcctAPIResponseException('Invalid password', 401)
    assert error.reason == 'Invalid password'
    assert error.code == 401
    assert str(error) == 'Invalid password (Error Code 401)'

    error = exc.AppleAcctAPIResponseException('Retry', 500, retry=True)
    assert str(error).endswith('. Retrying ...')

    error = exc.AppleAcctAPIResponseException(None)
    assert str(error) == 'Could not connect to iCloud Location Servers'


def test_2sa_exception_requires_the_apple_id() -> None:
    exc = exceptions_module()

    error = exc.AppleAcct2SARequiredException('someone@example.com')
    assert 'someone@example.com' in str(error)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#   The classes are defined once and re-exported by both modules
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def test_exception_classes_are_not_redefined() -> None:
    expected = {
        'AppleAcctException',
        'AppleAcctAPIResponseException',
        'AppleAcctManagerNotActivatedException',
        'AppleAcctFailedLoginException',
        'AppleAcct2FARequiredException',
        'AppleAcct2SARequiredException',
        'AppleAcctNoStoredPasswordAvailableException',
        'AppleAcctNoDevicesException',
    }

    defined: list[str] = []
    for relative_path in ("apple_acct/apple_acct.py",
                          "apple_acct/icloud_session.py",
                          "apple_acct/exceptions.py"):
        tree = tree_of(relative_path)
        defined += [node.name for node in ast.walk(tree)
                    if isinstance(node, ast.ClassDef)
                    and node.name.startswith('AppleAcct')
                    and node.name.endswith('Exception')]

    assert sorted(defined) == sorted(expected)


def test_both_modules_import_the_shared_exceptions() -> None:
    for relative_path in ("apple_acct/apple_acct.py",
                          "apple_acct/icloud_session.py"):
        tree = tree_of(relative_path)
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == 'exceptions':
                imported.update(alias.name for alias in node.names)

        assert 'AppleAcctException' in imported, relative_path
        assert 'AppleAcctAPIResponseException' in imported, relative_path
        assert 'AppleAcctNoDevicesException' in imported, relative_path


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#   icloud_session._raise_error
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def test_raise_error_can_actually_raise() -> None:
    function = function_named(tree_of("apple_acct/icloud_session.py"), "_raise_error")

    # A top-level 'return' before the raise is what made it dead code.
    assert not any(isinstance(node, ast.Return) for node in function.body)

    last = function.body[-1]
    assert 'raise api_error' in ast.unparse(last)


def test_retry_path_catches_the_base_exception() -> None:
    source = source_of("apple_acct/icloud_session.py")

    # authenticate() raises AppleAcctFailedLoginException for a bad password,
    # which is not an AppleAcctAPIResponseException.
    assert "except AppleAcctException as err" in source
    assert "except AppleAcctAPIResponseException" not in source


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#   Missing device fields
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def test_device_refresh_reads_model_fields_safely() -> None:
    tree = tree_of("apple_acct/apple_acct_devices.py")

    for node in ast.walk(tree):
        if (isinstance(node, ast.Subscript)
                and isinstance(node.value, ast.Name)
                and node.value.id == "device_data"
                and isinstance(node.slice, ast.Constant)
                and node.slice.value in ("modelDisplayName", "rawDeviceModel")):
            raise AssertionError(
                f"device_data[{node.slice.value!r}] raises KeyError for a device "
                f"that omits the field")


def test_device_loop_skips_a_device_that_fails() -> None:
    function = function_named(tree_of("apple_acct/apple_acct_devices.py"),
                              "update_device_location_data")

    device_loop = next(
        node for node in ast.walk(function)
        if isinstance(node, ast.For)
        and any(isinstance(child, ast.Name) and child.id == "devices_data"
                for child in ast.walk(node.iter)))

    assert any(isinstance(node, ast.Try) and node.handlers
               for node in device_loop.body), \
        "the per-device work is not isolated, one bad payload stops the loop"


def test_family_share_device_uses_get() -> None:
    function = function_named(tree_of("apple_acct/apple_acct_device_data.py"),
                              "family_share_device")

    assert not any(isinstance(node, ast.Subscript) for node in ast.walk(function))
    assert ".get('fmlyShare'" in ast.unparse(function)


def test_device_status_conversion_is_tolerant() -> None:
    function = function_named(tree_of("apple_acct/apple_acct_device_data.py"),
                              "_device_status_from_data")
    handled = set()
    for node in ast.walk(function):
        if isinstance(node, ast.ExceptHandler) and isinstance(node.type, ast.Tuple):
            handled.update(ast.unparse(element) for element in node.type.elts)

    assert {'TypeError', 'ValueError'} <= handled


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#   icloud_requests_io - auth errors are visible, not swallowed
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def test_request_io_imports_the_shared_exception() -> None:
    tree = tree_of("apple_acct/icloud_requests_io.py")
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == 'exceptions':
            imported.update(alias.name for alias in node.names)

    assert 'AppleAcctException' in imported


def test_request_io_reraise_is_gated_by_raise_api_errors() -> None:
    tree = tree_of("apple_acct/icloud_requests_io.py")

    for name in ("post", "get", "put"):
        function = function_named(tree, name)
        handlers = [handler
                    for node in ast.walk(function)
                    if isinstance(node, ast.Try)
                    for handler in node.handlers
                    if ast.unparse(handler.type) == "AppleAcctException"]

        assert handlers, f"{name}() does not catch AppleAcctException separately"
        assert any(isinstance(node, ast.Raise) for node in ast.walk(handlers[0])), \
            f"{name}() can never re-raise an AppleAcctException"
        assert "raise_api_errors" in ast.unparse(handlers[0]), \
            f"{name}() re-raises without checking AppleAcct.raise_api_errors"


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#   authenticate_with_password - the API error branch is reachable
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def test_password_auth_sets_and_clears_raise_api_errors() -> None:
    function = function_named(tree_of("apple_acct/apple_acct_auth.py"),
                              "authenticate_with_password")

    guarded = next(node for node in ast.walk(function)
                   if isinstance(node, ast.Try)
                   and any(ast.unparse(handler.type) == "AppleAcctAPIResponseException"
                           for handler in node.handlers))

    body = ast.unparse(ast.Module(body=guarded.body, type_ignores=[]))
    assert "self.raise_api_errors = True" in body
    assert "icloud_io.post" in body

    finalbody = ast.unparse(ast.Module(body=guarded.finalbody, type_ignores=[]))
    assert "self.raise_api_errors = False" in finalbody


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#   Device payload tolerance
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def test_create_AADeviceData_objects_isolates_each_device() -> None:
    function = function_named(tree_of("apple_acct/apple_acct_devices.py"),
                              "_create_AADeviceData_objects")

    device_loop = next(
        node for node in ast.walk(function)
        if isinstance(node, ast.For)
        and any(isinstance(child, ast.Name) and child.id == "devices_data"
                for child in ast.walk(node.iter)))

    assert any(isinstance(node, ast.Try) and node.handlers
               for node in device_loop.body), \
        "the per-device work is not isolated, one bad device stops the rest"


def test_start_ic3_reads_fmlyShare_safely() -> None:
    tree = tree_of("startup/start_ic3_apple.py")

    for node in ast.walk(tree):
        if (isinstance(node, ast.Subscript)
                and isinstance(node.slice, ast.Constant)
                and node.slice.value == "fmlyShare"):
            raise AssertionError(
                "device_data['fmlyShare'] raises KeyError for a device that "
                "omits the field")

    assert ".get('fmlyShare'" in source_of("startup/start_ic3_apple.py")


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#   Apple Acct reauth repair issue
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def test_reauth_repair_message_points_at_the_configure_screen() -> None:
    assert "Configure > Authenticate Apple Account" in \
        source_of("apple_acct/apple_acct_support.py")


def test_repair_issue_id_is_dropped_even_if_clearing_fails() -> None:
    function = function_named(tree_of("apple_acct/apple_acct_support.py"),
                              "_clear_apple_reauth_repair_issue")

    guarded = next(node for node in ast.walk(function)
                   if isinstance(node, ast.Try) and node.finalbody)

    assert 'clear_repair_issue' in ast.unparse(guarded)
    assert 'discard' in ast.unparse(guarded.finalbody)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#   Auth and session mixins - the manager is split, not copied
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
MOVED_TO_AUTH = (
    'authenticate',
    '_authenticate_with_token',
    'log_into_account',
    'authenticate_with_password',
    'authenticate_with_password_srp',
    '_srp_icloud_io_signin_init',
    '_srp_icloud_io_signin_complete',
    '_srp_icloud_io',
    'validate_upw_via_srp',
    '_set_srp_return_error_code',
    'setup_error',
    '_handle_accept_terms_of_use',
    '_handle_accept_terms_of_use_error',
    '_use_srp_signin_token_info',
)

MOVED_TO_SESSION = (
    'trust_token_expire_date_time',
    'set_trust_token_expire_in_days',
    '_validate_token',
    'is_session_trusted_auth_check',
    'is_session_still_trusted',
    'is_2fa_challenge_session_live',
    'get_auth_headers',
    'get_trusted_devices',
    '_read_session_data',
    '_setup_iCloudSession',
    'load_cookies',
    'list_cookies',
    'delete_cookie_and_session_files',
    'delete_trust_cookie',
    'read_token_pw_file',
    '_update_token_pw_session_data',
    '_update_token_pw',
    '_write_token_pw_file',
    'cookie_username_base',
    'cookies_filename',
    'cookies_filename_short',
    'session_filename',
    'session_filename_short',
)


def class_named(tree: ast.Module, name: str) -> ast.ClassDef:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node

    raise AssertionError(f"class {name} not found")


def method_names(class_node: ast.ClassDef) -> list[str]:
    return [node.name for node in class_node.body
            if isinstance(node, ast.FunctionDef)]


def test_the_mixins_are_plain_classes() -> None:
    auth_class = class_named(tree_of("apple_acct/apple_acct_auth.py"),
                             "AppleAcctAuthMixin")
    session_class = class_named(tree_of("apple_acct/apple_acct_session.py"),
                                "AppleAcctSessionMixin")

    # A mixin that inherits something of its own would reorder the manager's MRO.
    assert auth_class.bases == []
    assert session_class.bases == []


def test_the_manager_mixes_in_both_mixins() -> None:
    manager = class_named(tree_of("apple_acct/apple_acct.py"), "AppleAcctManager")

    # Order matters: auth methods are looked up before the session ones.
    assert [ast.unparse(base) for base in manager.bases] == [
        'AppleAcctAuthMixin', 'AppleAcctSessionMixin']

    imported = {(node.module, alias.name)
                for node in ast.walk(tree_of("apple_acct/apple_acct.py"))
                if isinstance(node, ast.ImportFrom)
                for alias in node.names}

    assert ('apple_acct_auth', 'AppleAcctAuthMixin') in imported
    assert ('apple_acct_session', 'AppleAcctSessionMixin') in imported


def test_moved_methods_are_defined_in_the_mixins_only() -> None:
    auth_methods = method_names(class_named(tree_of("apple_acct/apple_acct_auth.py"),
                                            "AppleAcctAuthMixin"))
    session_methods = method_names(class_named(tree_of("apple_acct/apple_acct_session.py"),
                                               "AppleAcctSessionMixin"))
    manager_methods = method_names(class_named(tree_of("apple_acct/apple_acct.py"),
                                               "AppleAcctManager"))

    for name in MOVED_TO_AUTH:
        assert name in auth_methods, f"{name}() is missing from AppleAcctAuthMixin"
        assert name not in manager_methods, f"{name}() is still defined in AppleAcctManager"

    for name in MOVED_TO_SESSION:
        assert name in session_methods, f"{name}() is missing from AppleAcctSessionMixin"
        assert name not in manager_methods, f"{name}() is still defined in AppleAcctManager"


def test_no_moved_method_is_defined_twice() -> None:
    defined: list[str] = []
    for relative_path in ("apple_acct/apple_acct.py",
                          "apple_acct/apple_acct_auth.py",
                          "apple_acct/apple_acct_session.py"):
        defined += [node.name for node in ast.walk(tree_of(relative_path))
                    if isinstance(node, ast.FunctionDef)]

    duplicated = sorted(name for name in MOVED_TO_AUTH + MOVED_TO_SESSION
                        if defined.count(name) != 1)

    assert duplicated == [], f"defined more than once: {duplicated}"


def test_new_mixins_do_not_import_the_manager_module() -> None:
    for relative_path in ("apple_acct/apple_acct_auth.py",
                          "apple_acct/apple_acct_session.py"):
        for node in ast.walk(tree_of(relative_path)):
            if isinstance(node, ast.ImportFrom):
                assert node.module != 'apple_acct', relative_path
                assert all(alias.name != 'AppleAcctManager' for alias in node.names), \
                    relative_path
            if isinstance(node, ast.Import):
                assert all('apple_acct' not in alias.name for alias in node.names), \
                    relative_path
