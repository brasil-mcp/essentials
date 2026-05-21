"""Validator de RENAVAM brasileiro (11 dígitos; aceita 9 ou 10 com padding à esquerda)."""

from __future__ import annotations

import re

from brasil_mcp.core.errors import ErrorCode, ErrorObj
from brasil_mcp.core.models import ValidationResult

_MASK_RE = re.compile(r"[^\d]")
_ALLOWED_CHARS_RE = re.compile(r"[^\d\s]")

_WEIGHTS = [2, 3, 4, 5, 6, 7, 8, 9, 2, 3]


def _format_renavam(digits: str) -> str:
    # RENAVAM has no canonical mask — return 11 digits.
    return digits


def _calc_digit(digits10: str) -> int:
    # Reverse the first 10 digits, multiply by weights [2..9, 2, 3], sum,
    # then dv = (sum * 10) % 11, with 10 collapsing to 0.
    rev = digits10[::-1]
    total = sum(int(c) * w for c, w in zip(rev, _WEIGHTS, strict=True))
    mod = (total * 10) % 11
    return 0 if mod == 10 else mod


def validate_renavam(value: str) -> ValidationResult:
    raw = value or ""
    if not raw.strip():
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.EMPTY_INPUT,
                "RENAVAM não pode ser vazio.",
                "RENAVAM cannot be empty.",
            ),
        )

    if _ALLOWED_CHARS_RE.search(raw):
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.INVALID_CHARACTER,
                "RENAVAM deve conter apenas dígitos.",
                "RENAVAM must contain only digits.",
            ),
        )

    digits = _MASK_RE.sub("", raw)

    # RENAVAM expanded from 9 to 11 digits; pad short inputs.
    if len(digits) == 9:
        digits = "00" + digits
    elif len(digits) == 10:
        digits = "0" + digits

    if len(digits) != 11:
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.INVALID_LENGTH,
                f"RENAVAM deve ter 9 a 11 dígitos; recebido {len(_MASK_RE.sub('', raw))}.",
                f"RENAVAM must have 9 to 11 digits; received {len(_MASK_RE.sub('', raw))}.",
                suggestion="Verifique se o número não está truncado.",
            ),
        )

    if len(set(digits)) == 1:
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.REPEATED_DIGITS,
                "RENAVAM com todos os dígitos iguais é inválido.",
                "RENAVAM with all repeated digits is invalid.",
            ),
        )

    dv = _calc_digit(digits[:10])
    if dv != int(digits[10]):
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.INVALID_CHECKSUM,
                "Dígito verificador do RENAVAM não confere.",
                "RENAVAM checksum digit does not match.",
            ),
        )

    return ValidationResult(valid=True, raw=raw, formatted=_format_renavam(digits))
