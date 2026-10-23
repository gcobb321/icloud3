"""Contracts for tracking fixes that cannot be imported without Home Assistant.

The tracking package imports the integration ``__init__`` (and Home Assistant),
so most checks read the source/AST. The Waze route validation is pure, so only
that function is compiled out of the module and exercised for real.
"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components/icloud3"
TRACKING = COMPONENT / "tracking"


def source_of(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def function_node(relative_path: str, name: str, class_name: str | None = None) -> ast.FunctionDef:
    tree = ast.parse(source_of(COMPONENT / relative_path))
    body = tree.body
    if class_name is not None:
        klass = next(node for node in body
                     if isinstance(node, ast.ClassDef) and node.name == class_name)
        body = klass.body

    for node in body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node

    raise AssertionError(f"{name} not found in {relative_path}")


def compile_function(relative_path: str, name: str, class_name: str | None = None,
                     namespace: dict | None = None) -> tuple:
    module = ast.Module(body=[function_node(relative_path, name, class_name)],
                        type_ignores=[])
    ast.fix_missing_locations(module)
    ns = {} if namespace is None else namespace
    exec(compile(module, relative_path, "exec"), ns)
    return ns[name], ns


def test_determine_interval_has_no_impossible_zero_gt_range() -> None:
    tree = ast.parse(source_of(TRACKING / "determine_interval.py"))

    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        if not (isinstance(node.left, ast.Constant) and node.left.value == 0):
            continue
        assert not (len(node.ops) == 2
                    and isinstance(node.ops[0], ast.Gt)
                    and isinstance(node.ops[1], ast.GtE)), \
            f"impossible comparison: {ast.unparse(node)}"


def test_determine_interval_battery_ranges_include_low_values() -> None:
    tree = ast.parse(source_of(TRACKING / "determine_interval.py"))

    assignments = {}
    for node in ast.walk(tree):
        if (isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)):
            assignments[node.targets[0].id] = ast.unparse(node.value)

    assert assignments["battery10_flag"] == "0 < Device.dev_data_battery_level <= 10"
    assert assignments["battery5_flag"] == "0 < Device.dev_data_battery_level <= 5"

    comparisons = [ast.unparse(node) for node in ast.walk(tree)
                   if isinstance(node, ast.Compare)]
    assert "0 < Device.dev_data_battery_level <= 33" in comparisons


def test_trigger_monitored_device_update_sets_event_msg() -> None:
    function = function_node("tracking/stationary_zone.py", "_trigger_monitored_device_update")

    assigned = [ast.unparse(node.value) for node in ast.walk(function)
                if isinstance(node, ast.Assign)
                and any(isinstance(target, ast.Name) and target.id == "event_msg"
                        for target in node.targets)]

    assert any("Enter New Stationary Zone > " in text for text in assigned)
    assert any("Exit Removed Stationary Zone > " in text for text in assigned)
    assert any(isinstance(node, ast.If) and ast.unparse(node.test) == "event_msg"
               for node in ast.walk(function))


def test_zone_tolerance_caps_gps_accuracy_adjustment() -> None:
    source = source_of(TRACKING / "zone_handler.py")
    capped = "min(int(Device.loc_data_gps_accuracy / 2), GPS_ACCURACY_MAX_ADJ_M)"

    assert "GPS_ACCURACY_MAX_ADJ_M = 100" in source
    assert source.count(capped) == 2
    assert "int(Device.loc_data_gps_accuracy / 2)" not in source.replace(capped, "")


WAZE_CONSTANTS = {
    "WAZE_USED": 0,
    "WAZE_NOT_USED": 1,
    "WAZE_PAUSED": 2,
    "WAZE_OUT_OF_RANGE": 3,
    "WAZE_NO_DATA": 4,
    "WAZE_NO_ROUTE": "no_route",
    "WAZE_RATE_LIMITED": "rate_limited",
    "ZONE": "zone",
    "WAZE_RETRY_ATTEMPTS": 1,
    "format_gps": lambda *args: "",
    "log_info_msg": lambda *args, **kwargs: None,
}


class FakeRouteCalculator:
    def __init__(self, route):
        self.route = route
        self.is_rate_limited = False
        self.waze_error_msg = ""

    def calc_route_info(self, *args):
        return self.route


class FakeWaze:
    def __init__(self, route):
        self.WazeRouteCalc = FakeRouteCalculator(route)
        self.no_route_msg_by_zone = {}
        self.internet_error_displayed = False
        self.cached = []
        self.paused = False
        self.no_route_displayed = False

    def _get_waze_cache(self, route_gps):
        return None

    def _set_waze_cache(self, *args):
        self.cached.append(args)

    def _pause_waze_rate_limited(self):
        self.paused = True

    def _display_no_route_msg(self, *args):
        self.no_route_displayed = True

    def _wait_before_waze_retry(self, retry_cnt, waited_secs):
        return waited_secs

    def _set_waze_not_available_error(self, err):
        pass


class FakeFromZone:
    from_zone = "not_home"
    from_zone_dname = "Away"


def waze_get_waze_distance():
    is_valid_route, _ = compile_function("tracking/waze.py", "is_valid_route")
    namespace = dict(WAZE_CONSTANTS)
    namespace["is_valid_route"] = is_valid_route
    function, _ = compile_function("tracking/waze.py", "get_waze_distance",
                                   class_name="Waze", namespace=namespace)
    return function, is_valid_route


def test_waze_is_valid_route_rejects_zero_time_or_distance() -> None:
    _, is_valid_route = waze_get_waze_distance()

    assert is_valid_route(12.0, 5.0)
    assert is_valid_route(0.25, 0.4)
    assert not is_valid_route(0.0, 0.0)
    assert not is_valid_route(0.0, 5.0)
    assert not is_valid_route(12.0, 0.0)
    assert not is_valid_route(-1.0, 5.0)


def test_waze_zero_route_returns_no_data_and_is_not_cached() -> None:
    function, _ = waze_get_waze_distance()
    fake_waze = FakeWaze((0.0, 0.0))

    result = function(fake_waze, None, FakeFromZone(), 1.0, 1.0, 2.0, 2.0, "zone")

    assert result == (WAZE_CONSTANTS["WAZE_NO_DATA"], 0, 0)
    assert fake_waze.cached == []


def test_waze_valid_route_is_used_and_cached() -> None:
    function, _ = waze_get_waze_distance()
    fake_waze = FakeWaze((12.5, 8.25))

    result = function(fake_waze, None, FakeFromZone(), 1.0, 1.0, 2.0, 2.0, "zone")

    assert result == (WAZE_CONSTANTS["WAZE_USED"], 12.5, 8.25)
    assert len(fake_waze.cached) == 1


def test_waze_rate_limit_and_no_route_exits_are_preserved() -> None:
    function, _ = waze_get_waze_distance()

    rate_limited = FakeWaze((-1.0, 0.0))
    rate_limited.WazeRouteCalc.is_rate_limited = True
    assert function(rate_limited, None, FakeFromZone(), 1.0, 1.0, 2.0, 2.0, "zone") \
        == (WAZE_CONSTANTS["WAZE_RATE_LIMITED"], 0, 0)
    assert rate_limited.paused

    no_route = FakeWaze((-1.0, 0.0))
    no_route.WazeRouteCalc.waze_error_msg = "Internal Error"
    assert function(no_route, None, FakeFromZone(), 1.0, 1.0, 2.0, 2.0, "zone") \
        == (WAZE_CONSTANTS["WAZE_NO_ROUTE"], 0, 0)
    assert no_route.no_route_displayed


def test_waze_rejects_invalid_route_before_caching() -> None:
    function = function_node("tracking/waze.py", "get_waze_distance", class_name="Waze")

    checks = []
    for node in ast.walk(function):
        if not isinstance(node, ast.If):
            continue
        test = node.test
        if (isinstance(test, ast.UnaryOp)
                and isinstance(test.op, ast.Not)
                and isinstance(test.operand, ast.Call)
                and isinstance(test.operand.func, ast.Name)
                and test.operand.func.id == "is_valid_route"):
            checks.append(node)

    assert checks, "get_waze_distance must validate the route"

    for check in checks:
        returns = [node for node in ast.walk(check) if isinstance(node, ast.Return)]
        assert any(
            isinstance(node.value, ast.Tuple)
            and isinstance(node.value.elts[0], ast.Name)
            and node.value.elts[0].id == "WAZE_NO_DATA"
            for node in returns
        ), "an invalid route must return WAZE_NO_DATA"
