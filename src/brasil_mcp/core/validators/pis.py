"""Validator de PIS/PASEP/NIT brasileiro (11 dígitos, módulo 11)."""

from __future__ import annotations

import re

from brasil_mcp.core.errors import ErrorCode, ErrorObj
from brasil_mcp.core.models import ValidationResult

_MASK_RE = re.compile(r"[^\d]")
_ALLOWED_CHARS_RE = re.compile(r"[^\d.\-\s]")

_WEIGHTS = [3, 2, 9, 8, 7, 6, 5, 4, 3, 2]


def _format_pis(digits: str) -> str:
    # XXX.XXXXX.XX-X (3-5-2-1)
    return f"{digits[:3]}.{digits[3:8]}.{digits[8:10]}-{digits[10]}"


def _calc_digit(digits10: str) -> int:
    total = sum(int(d) * w for d, w in zip(digits10, _WEIGHTS, strict=True))
    rem = total % 11
    return 0 if rem < 2 else 11 - rem


def validate_pis(value: str) -> ValidationResult:
    raw = value or ""
    if not raw.strip():
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.EMPTY_INPUT,
                "PIS não pode ser vazio.",
                "PIS cannot be empty.",
            ),
        )

    if _ALLOWED_CHARS_RE.search(raw):
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.INVALID_CHARACTER,
                "PIS deve conter apenas dígitos e máscara opcional.",
                "PIS must contain only digits and optional mask.",
            ),
        )

    digits = _MASK_RE.sub("", raw)

    if len(digits) != 11:
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.INVALID_LENGTH,
                f"PIS deve ter 11 dígitos; recebido {len(digits)}.",
                f"PIS must have 11 digits; received {len(digits)}.",
                suggestion="Verifique se o número não está truncado.",
            ),
        )

    if len(set(digits)) == 1:
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.REPEATED_DIGITS,
                "PIS com todos os dígitos iguais é inválido.",
                "PIS with all repeated digits is invalid.",
            ),
        )

    dv = _calc_digit(digits[:10])
    if dv != int(digits[10]):
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.INVALID_CHECKSUM,
                "Dígito verificador do PIS não confere.",
                "PIS checksum digit does not match.",
            ),
        )

    return ValidationResult(valid=True, raw=raw, formatted=_format_pis(digits))
