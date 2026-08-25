from __future__ import annotations

import pytest

from moomoo_market_data.config import OpenDConfig


def test_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FUTU_OPEND_HOST", raising=False)
    monkeypatch.delenv("FUTU_OPEND_PORT", raising=False)
    assert OpenDConfig.from_env() == OpenDConfig()


def test_custom_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FUTU_OPEND_HOST", "192.168.1.10")
    monkeypatch.setenv("FUTU_OPEND_PORT", "22222")
    assert OpenDConfig.from_env() == OpenDConfig("192.168.1.10", 22222)


@pytest.mark.parametrize("value", ["0", "65536", "not-a-number"])
def test_invalid_port(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("FUTU_OPEND_PORT", value)
    with pytest.raises(ValueError):
        OpenDConfig.from_env()
