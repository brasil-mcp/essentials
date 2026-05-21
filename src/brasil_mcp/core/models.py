"""Dataclasses de output usadas pelos core modules."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from brasil_mcp.core.errors import ErrorObj


@dataclass(frozen=True, slots=True)
class ValidationResult:
    valid: bool
    raw: str
    formatted: str | None = None
    error: ErrorObj | None = None
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "valid": self.valid,
            "formatted": self.formatted,
            "raw": self.raw,
            "error": self.error.to_dict() if self.error else None,
        }
        result.update(self.extras)
        return result
