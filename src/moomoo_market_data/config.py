"""Runtime configuration for Futu OpenD."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OpenDConfig:
    host: str = "127.0.0.1"
    port: int = 11111

    @classmethod
    def from_env(cls) -> "OpenDConfig":
        host = os.getenv("FUTU_OPEND_HOST", "127.0.0.1").strip()
        if not host:
            raise ValueError("FUTU_OPEND_HOST cannot be empty")
        raw_port = os.getenv("FUTU_OPEND_PORT", "11111").strip()
        try:
            port = int(raw_port)
        except ValueError as exc:
            raise ValueError("FUTU_OPEND_PORT must be an integer") from exc
        if not 1 <= port <= 65535:
            raise ValueError("FUTU_OPEND_PORT must be between 1 and 65535")
        return cls(host=host, port=port)
