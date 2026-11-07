"""Regression tests for add_log_file_filter in utils/messaging.py.

The Home Assistant integration under test imports the ``homeassistant`` package at
module import time. Home Assistant is not installed in this environment, so the
minimal parts of it that are actually touched by the import chain are stubbed out
below, and the heavy ``custom_components.icloud3.__init__`` is bypassed.
"""

import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def _install_fake_homeassistant():
    """Register minimal fake homeassistant modules needed to import messaging."""

    def _module(name, **attrs):
        module = ModuleType(name)
        for key, value in attrs.items():
            setattr(module, key, value)
        sys.modules[name] = module
        return module

    _module("homeassistant")
    _module("homeassistant.util")
    _module("homeassistant.util.dt")
    _module("homeassistant.components")
    _module("homeassistant.components.persistent_notification")
    _module("homeassistant.const", STATE_HOME="home", STATE_NOT_HOME="not_home")


def _install_fake_icloud3_package():
    """Register a stub 'custom_components.icloud3' package pointing at the real
    source tree so the relative imports inside messaging.py resolve without ever
    executing the integration's top-level __init__.py (which needs full HA)."""

    custom_components = ModuleType("custom_components")
    custom_components.__path__ = [str(REPO_ROOT / "custom_components")]
    sys.modules["custom_components"] = custom_components

    icloud3 = ModuleType("custom_components.icloud3")
    icloud3.__path__ = [str(REPO_ROOT / "custom_components" / "icloud3")]
    sys.modules["custom_components.icloud3"] = icloud3


_install_fake_homeassistant()
_install_fake_icloud3_package()

from custom_components.icloud3.utils import messaging  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_filter_state():
    messaging.Gb.upw_filter_items.clear()
    messaging.Gb.upw_unfilter_items.clear()
    yield
    messaging.Gb.upw_filter_items.clear()
    messaging.Gb.upw_unfilter_items.clear()


def test_add_log_file_filter_short_prefix_before_at_does_not_raise():
    """A value containing '@' with a prefix shorter than 3 characters must not
    raise IndexError (regression for email_id[-3] on e.g. 'a@')."""
    # Length >= 6, contains '@', part before '@' is only one character.
    messaging.add_log_file_filter("a@12345")


@pytest.mark.parametrize(
    "value",
    [
        "a@12345",
        "ab@1234",
        "abc@123",
        "geekstergary@domain.com",
    ],
)
def test_add_log_file_filter_email_like_values_do_not_raise(value):
    messaging.add_log_file_filter(value)
