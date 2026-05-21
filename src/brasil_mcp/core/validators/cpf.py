"""Validator de CPF brasileiro (11 dígitos, módulo 11)."""

from __future__ import annotations

import re

from brasil_mcp.core.errors import ErrorCode, ErrorObj
from brasil_mcp.core.models import ValidationResult

_MASK_RE = re.compile(r"[^\d]")
_ALLOWED_CHARS_RE = re.compile(r"[^\d.\-\s]")


def _format_cpf(digits: str) -> str:
    return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"


def _calc_digit(digits: str, weight_start: int) -> int:
    weights = range(weight_start, 1, -1)
    total = sum(int(d) * w for d, w in zip(digits, weights, strict=True))
    rem = total % 11
    return 0 if rem < 2 else 11 - rem


def validate_cpf(value: str) -> ValidationResult:
    raw = value or ""
    if not raw.strip():
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.EMPTY_INPUT,
                "CPF não pode ser vazio.",
                "CPF cannot be empty.",
            ),
        )

    if _ALLOWED_CHARS_RE.search(raw):
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.INVALID_CHARACTER,
                "CPF deve conter apenas dígitos e máscara opcional.",
                "CPF must contain only digits and optional mask.",
            ),
        )

    digits = _MASK_RE.sub("", raw)

    if len(digits) != 11:
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.INVALID_LENGTH,
                f"CPF deve ter 11 dígitos; recebido {len(digits)}.",
                f"CPF must have 11 digits; received {len(digits)}.",
                suggestion="Verifique se o número não está truncado.",
            ),
        )

    if len(set(digits)) == 1:
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.REPEATED_DIGITS,
                "CPF com todos os dígitos iguais é inválido.",
                "CPF with all repeated digits is invalid.",
            ),
        )

    d1 = _calc_digit(digits[:9], weight_start=10)
    d2 = _calc_digit(digits[:10], weight_start=11)
    if d1 != int(digits[9]) or d2 != int(digits[10]):
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.INVALID_CHECKSUM,
                "Dígitos verificadores do CPF não conferem.",
                "CPF checksum digits do not match.",
            ),
        )

    return ValidationResult(valid=True, raw=raw, formatted=_format_cpf(digits))
