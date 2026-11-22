import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from support import harness as h
from support import scenarios as st

h.install_network_guard()
h.prepare_code_copy()


def pytest_report_header(config):
    return f"iCloud3 code under test: {h.CODE_DIR}/custom_components/icloud3, work dir {h.WORK}"


@pytest.fixture(autouse=True)
def report_harness_gaps(request):
    '''A test failing on a FakeAppleAcct/FakeDevice gap is a test problem, say so'''
    st.FAKE_MISSING_ATTRS.clear()
    h.NETWORK_ATTEMPTS.clear()
    yield
    if st.FAKE_MISSING_ATTRS:
        print(f"\nTEST HARNESS GAP in {request.node.name}: the fake objects miss "
              f"{sorted(st.FAKE_MISSING_ATTRS)}")
