"""Validator de CNH brasileira (11 dígitos, módulo 11 com dois DVs)."""

from __future__ import annotations

import re

from brasil_mcp.core.errors import ErrorCode, ErrorObj
from brasil_mcp.core.models import ValidationResult

_MASK_RE = re.compile(r"[^\d]")
_ALLOWED_CHARS_RE = re.compile(r"[^\d\s]")


def _format_cnh(digits: str) -> str:
    # CNH has no canonical mask — return 11 digits.
    return digits


def _calc_digits(digits9: str) -> tuple[int, int]:
    # DV1: weights 9..1 (decreasing).
    s1 = sum(int(c) * (9 - i) for i, c in enumerate(digits9))
    r1 = s1 % 11
    if r1 >= 10:
        dv1 = 0
        dsc = 2
    else:
        dv1 = r1
        dsc = 0

    # DV2: weights 1..9 (increasing), apply DV1 discount.
    s2 = sum(int(c) * (i + 1) for i, c in enumerate(digits9))
    r2 = (s2 % 11) - dsc
    if r2 < 0:
        r2 += 11
    dv2 = 0 if r2 >= 10 else r2
    return dv1, dv2


def validate_cnh(value: str) -> ValidationResult:
    raw = value or ""
    if not raw.strip():
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.EMPTY_INPUT,
                "CNH não pode ser vazia.",
                "CNH cannot be empty.",
            ),
        )

    if _ALLOWED_CHARS_RE.search(raw):
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.INVALID_CHARACTER,
                "CNH deve conter apenas dígitos.",
                "CNH must contain only digits.",
            ),
        )

    digits = _MASK_RE.sub("", raw)

    if len(digits) != 11:
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.INVALID_LENGTH,
                f"CNH deve ter 11 dígitos; recebido {len(digits)}.",
                f"CNH must have 11 digits; received {len(digits)}.",
                suggestion="Verifique se o número não está truncado.",
            ),
        )

    if len(set(digits)) == 1:
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.REPEATED_DIGITS,
                "CNH com todos os dígitos iguais é inválida.",
                "CNH with all repeated digits is invalid.",
            ),
        )

    dv1, dv2 = _calc_digits(digits[:9])
    if dv1 != int(digits[9]) or dv2 != int(digits[10]):
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.INVALID_CHECKSUM,
                "Dígitos verificadores da CNH não conferem.",
                "CNH checksum digits do not match.",
            ),
        )

    return ValidationResult(valid=True, raw=raw, formatted=_format_cnh(digits))
