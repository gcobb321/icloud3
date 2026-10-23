"""Secret and location redaction must be safe by default."""

from __future__ import annotations


def test_text_masks_bearer_token(redact) -> None:
    text = "Authorization: Bearer abc.def-123"
    result = redact.redact_text(text)
    assert "abc.def-123" not in result
    assert "**REDACTED**" in result


def test_text_masks_email_and_coordinates(redact) -> None:
    result = redact.redact_text("user@example.com at 41.12345, 29.98765")
    assert "user@example.com" not in result
    assert "41.12345" not in result
    assert "29.98765" not in result


def test_mapping_masks_sensitive_keys_recursively(redact) -> None:
    payload = {
        "username": "person@example.com",
        "password": "secret",
        "nested": {"access_token": "token-value", "safe": 1},
        "list": [{"latitude": 41.0, "name": "x"}],
    }
    result = redact.redact_mapping(payload)

    assert result["username"] == redact.REDACTED
    assert result["password"] == redact.REDACTED
    assert result["nested"]["access_token"] == redact.REDACTED
    assert result["nested"]["safe"] == 1
    assert result["list"][0]["latitude"] == redact.REDACTED
    assert result["list"][0]["name"] == "x"


def test_cycle_is_not_recursive(redact) -> None:
    payload: dict = {}
    payload["self"] = payload
    result = redact.redact_mapping(payload)
    assert result["self"] == redact.CYCLE


def test_assignment_style_secret_is_masked(redact) -> None:
    result = redact.redact_text("session_token=abc123; trust_token=def456")
    assert "abc123" not in result
    assert "def456" not in result
    assert result.count("**REDACTED**") == 2
