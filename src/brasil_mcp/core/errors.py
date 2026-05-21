"""Códigos de erro e ErrorObj usados por todos os core modules."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ErrorCode(StrEnum):
    INVALID_FORMAT = "INVALID_FORMAT"
    INVALID_LENGTH = "INVALID_LENGTH"
    INVALID_CHECKSUM = "INVALID_CHECKSUM"
    EMPTY_INPUT = "EMPTY_INPUT"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    VALUE_TOO_LONG = "VALUE_TOO_LONG"
    INVALID_CHARACTER = "INVALID_CHARACTER"
    INVALID_DATE = "INVALID_DATE"
    REPEATED_DIGITS = "REPEATED_DIGITS"


@dataclass(frozen=True, slots=True)
class ErrorObj:
    code: ErrorCode
    message_pt: str
    message_en: str
    suggestion: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "code": str(self.code),
            "message_pt": self.message_pt,
            "message_en": self.message_en,
            "suggestion": self.suggestion,
        }
