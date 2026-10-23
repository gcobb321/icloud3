"""Home Assistant test harness for iCloud3.

These tests import the real integration with the HA test fixtures. They are
separate from the Home-Assistant-free unit tests so the fast suite stays fast.
"""

from __future__ import annotations

import pytest

pytest_plugins = ["pytest_homeassistant_custom_component"]


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Let HA discover custom_components in this repository."""
    yield
