"""Mocked regression tests for the iCloud3 Waze HTTP 403 fallback."""
from __future__ import annotations

import importlib.util
import os
import sys
import types
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

SOURCE = Path(__file__).resolve().parents[1] / 'custom_components/icloud3/tracking/waze_route_calc_ic3.py'
MANIFEST = Path(__file__).resolve().parents[1] / 'custom_components/icloud3/manifest.json'

class Response:
    def __init__(self, status: int, payload=None, *, raises=None):
        self.status_code = status
        self.ok = 200 <= status < 300
        self.payload = payload
        self.raises = raises

    def json(self):
        if self.raises:
            raise self.raises
        return self.payload

class FakeSession:
    def __init__(self, result):
        self.result = result
        self.get_calls = []
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.closed = True

    def get(self, *args, **kwargs):
        self.get_calls.append((args, kwargs))
        if isinstance(self.result, Exception):
            raise self.result
        return self.result

@pytest.fixture
def mod(monkeypatch):
    package = 'fake_icloud3'
    for name in (package, package+'.utils', package+'.tracking'):
        module = types.ModuleType(name)
        module.__path__ = []
        monkeypatch.setitem(sys.modules, name, module)
    log = types.ModuleType(package+'.utils.messaging')
    log.log_exception = Mock()
    log.log_warning_msg = Mock()
    log.log_error_msg = Mock()
    log.log_info_msg = Mock()
    log._log = Mock()
    monkeypatch.setitem(sys.modules, package+'.utils.messaging', log)
    spec = importlib.util.spec_from_file_location(package+'.tracking.waze_route_calc_ic3', SOURCE)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)
    return module

@pytest.fixture
def installed_curl(monkeypatch):
    created = []
    responses = []
    def make_session(*, impersonate):
        assert impersonate == 'chrome'
        session = FakeSession(responses.pop(0))
        created.append(session)
        return session
    fake_module=types.ModuleType('curl_cffi')
    fake_module.requests=types.SimpleNamespace(Session=make_session)
    monkeypatch.setitem(sys.modules, 'curl_cffi', fake_module)
    return responses, created

def test_manifest_has_dependency():
    import json
    obj=json.loads(MANIFEST.read_text())
    assert 'curl-cffi>=0.13.0' in obj['requirements']

def test_israel_server_routing_correct(mod):
    with patch.object(mod.requests, 'get',return_value=Response(200,{'response':{'results':[]}})) as request:
        route=mod.WazeRouteCalculator('IL',True).get_route(31.77,35.21,31.79,35.23)
    assert route == {'results': []}
    args,opts=request.call_args
    assert args[0]=='https://routing-livemap-il.waze.com/RoutingManager/routingRequest'
    assert opts['params']['from']=='x:35.21 y:31.77'
    assert opts['params']['to']=='x:35.23 y:31.79'
    assert opts['timeout']==60
    assert opts['headers']['referer']=='https://www.waze.com/'

def test_http_200_does_not_invoke_fallback(mod, installed_curl):
    responses, sessions=installed_curl
    with patch.object(mod.requests,'get',return_value=Response(200,{'response':{'results':[]}})):
        assert mod.WazeRouteCalculator('IL',True).get_route(31.7,35.2,31.8,35.3)
    assert not sessions

def test_403_successful_retry_with_fresh_chrome_session(mod, installed_curl):
    responses,sessions=installed_curl
    responses.append(Response(200,{'response':{'results':[{'length':12000,'crossTime':900}]}}))
    with patch.object(mod.requests,'get',return_value=Response(403)) as request:
        result=mod.WazeRouteCalculator('IL',True).calc_route_info(31.7,35.2,31.8,35.3,log_results_flag=False)
    assert result==(15.0,12.0)
    assert len(sessions)==1
    assert sessions[0].closed
    assert sessions[0].get_calls[0][0][0] == request.call_args.args[0]
    assert sessions[0].get_calls[0][1]['params'] == request.call_args.kwargs['params']
    assert sessions[0].get_calls[0][1]['headers'] == request.call_args.kwargs['headers']
    assert sessions[0].get_calls[0][1]['timeout'] == 60

def test_repeated_403_uses_different_sessions(mod,installed_curl):
    responses,sessions=installed_curl
    responses.extend([Response(200,{'response':{'results':[]}}),Response(200,{'response':{'results':[]}})])
    with patch.object(mod.requests,'get',return_value=Response(403)):
        calc=mod.WazeRouteCalculator('IL',True)
        calc.get_route(31.7,35.2,31.8,35.3)
        calc.get_route(31.7,35.2,31.8,35.3)
    assert len(sessions)==2
    assert sessions[0] is not sessions[1]
    assert all(x.closed for x in sessions)

def test_non_403_failure_has_no_fallback(mod,installed_curl):
    _,sessions=installed_curl
    with patch.object(mod.requests,'get',return_value=Response(500)):
        assert mod.WazeRouteCalculator('IL',True).get_route(31.7,35.2,31.8,35.3) is None
    assert not sessions

def test_403_fallback_still_forbidden_returns_no_data(mod,installed_curl):
    responses,sessions=installed_curl
    responses.append(Response(403))
    with patch.object(mod.requests,'get',return_value=Response(403)):
        assert mod.WazeRouteCalculator('IL',True).calc_route_info(31.7,35.2,31.8,35.3,False)==(-1,-1)
    assert len(sessions)==1
    assert sessions[0].closed

def test_403_fallback_network_error_returns_no_data(mod,installed_curl):
    responses,sessions=installed_curl
    responses.append(TimeoutError('Waze timed out'))
    with patch.object(mod.requests,'get',return_value=Response(403)):
        assert mod.WazeRouteCalculator('IL',True).get_route(31.7,35.2,31.8,35.3) is None
    assert sessions[0].closed

def test_initial_network_error_does_not_raise_unbound_variable(mod):
    with patch.object(mod.requests,'get',side_effect=TimeoutError('connection timed out')):
        assert mod.WazeRouteCalculator('IL',True).calc_route_info(31.7,35.2,31.8,35.3,False)==(-1,-1)

def test_malformed_payload_returns_no_data(mod):
    with patch.object(mod.requests,'get',return_value=Response(200,raises=ValueError('invalid JSON'))):
        assert mod.WazeRouteCalculator('IL',True).get_route(31.7,35.2,31.8,35.3) is None

def test_missing_response_or_empty_list_returns_no_data(mod):
    with patch.object(mod.requests,'get',side_effect=[Response(200,{}),Response(200,{'response':[]})]):
        calc=mod.WazeRouteCalculator('IL',True)
        assert calc.get_route(31.7,35.2,31.8,35.3) is None
        assert calc.get_route(31.7,35.2,31.8,35.3) is None

def test_legacy_and_new_results_schema(mod):
    segment={'length':1000,'crossTime':60,'crossTimeWithoutRealTime':45}
    payloads=[{'response': {'results':[segment]}}, {'response': {'result':[segment]}}]
    with patch.object(mod.requests,'get',side_effect=[Response(200,x) for x in payloads]):
        calc=mod.WazeRouteCalculator('IL',False)
        assert calc.calc_route_info(31.7,35.2,31.8,35.3,False)==(.75,1)
        assert calc.calc_route_info(31.7,35.2,31.8,35.3,False)==(.75,1)

def test_server_json_error_returns_no_route(mod):
    with patch.object(mod.requests, 'get', return_value=Response(200, {'error': 'Route unavailable'})):
        assert mod.WazeRouteCalculator('IL', True).get_route(31.7, 35.2, 31.8, 35.3) is None

def test_list_wrapped_response(mod):
    with patch.object(mod.requests, 'get', return_value=Response(200, {'response': [{'results': [{'length': 3000, 'crossTime': 180}]}]})):
        assert mod.WazeRouteCalculator('IL', True).calc_route_info(31.7, 35.2, 31.8, 35.3, False) == (3.0, 3.0)


@pytest.mark.skipif(os.getenv('ICLOUD3_WAZE_LIVE_TEST') != '1', reason='Live Waze smoke test is opt-in (set ICLOUD3_WAZE_LIVE_TEST=1)')
def test_live_waze_israel_returns_route(mod):
    """Contact the real IL routing endpoint with public coordinates, never private device locations.

    This is intentionally not part of automated CI to avoid unreliable external
    traffic. Run with ICLOUD3_WAZE_LIVE_TEST=1 after installing dependencies.
    """
    # Synthetic/public city-center positions around Tel Aviv, Israel.
    minutes, distance_km = mod.WazeRouteCalculator('IL', True).calc_route_info(
        32.0853, 34.7818, 32.0741, 34.7920, log_results_flag=False,
    )
    assert minutes > 0, 'Waze did not return a usable travel time'
    assert distance_km > 0, 'Waze did not return a usable driving distance'
