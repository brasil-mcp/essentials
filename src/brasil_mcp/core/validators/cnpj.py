"""Validator de CNPJ — legacy (14 dígitos) E alfanumérico (RF NT COCAD/SUARA 49/2024)."""

from __future__ import annotations

import re

from brasil_mcp.core.errors import ErrorCode, ErrorObj
from brasil_mcp.core.models import ValidationResult

_MASK_RE = re.compile(r"[^A-Za-z0-9]")
_ALNUM_BASE_RE = re.compile(r"^[A-Z0-9]{12}$")
_LEGACY_BASE_RE = re.compile(r"^\d{12}$")
_ALLOWED_CHARS_RE = re.compile(r"[^A-Za-z0-9./\-\s]")

W1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
W2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]


def _format_cnpj(canonical: str) -> str:
    return f"{canonical[:2]}.{canonical[2:5]}.{canonical[5:8]}/{canonical[8:12]}-{canonical[12:]}"


def _char_value(c: str) -> int:
    """Map a character to its numeric value per RF NT COCAD/SUARA 49/2024.

    Digits '0'-'9' → 0-9 (ord 48..57 → 0..9).
    Letters 'A'-'Z' → 17-42 (ord 65..90 → 17..42).
    """
    return ord(c) - 48


def calc_digit(base: str, weights: list[int]) -> int:
    """Compute mod-11 check digit for a CNPJ base using given weights."""
    total = sum(_char_value(c) * w for c, w in zip(base, weights, strict=True))
    rem = total % 11
    return 0 if rem < 2 else 11 - rem


def validate_cnpj(value: str) -> ValidationResult:
    raw = value or ""
    if not raw.strip():
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.EMPTY_INPUT,
                "CNPJ não pode ser vazio.",
                "CNPJ cannot be empty.",
            ),
        )

    upper = raw.upper()
    if _ALLOWED_CHARS_RE.search(upper):
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.INVALID_CHARACTER,
                "CNPJ deve conter apenas letras/dígitos e máscara opcional.",
                "CNPJ must contain only letters/digits and optional mask.",
            ),
        )

    canon = _MASK_RE.sub("", upper)
    if len(canon) != 14:
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.INVALID_LENGTH,
                f"CNPJ deve ter 14 caracteres; recebido {len(canon)}.",
                f"CNPJ must have 14 chars; received {len(canon)}.",
            ),
        )

    base, dv = canon[:12], canon[12:]
    if not dv.isdigit():
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.INVALID_FORMAT,
                "Os dois dígitos verificadores do CNPJ devem ser numéricos.",
                "CNPJ check digits must be numeric.",
            ),
        )

    if _LEGACY_BASE_RE.match(base):
        cnpj_format = "legacy"
    elif _ALNUM_BASE_RE.match(base):
        cnpj_format = "alphanumeric"
    else:
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.INVALID_FORMAT,
                "Os 12 primeiros caracteres devem ser dígitos (legacy) ou alfanuméricos A-Z/0-9 (novo formato).",
                "First 12 chars must be digits (legacy) or alphanumeric A-Z/0-9 (new format).",
            ),
        )

    if len(set(canon)) == 1:
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.REPEATED_DIGITS,
                "CNPJ com todos os caracteres iguais é inválido.",
                "CNPJ with all repeated chars is invalid.",
            ),
        )

    d1 = calc_digit(base, W1)
    d2 = calc_digit(base + str(d1), W2)
    if str(d1) != dv[0] or str(d2) != dv[1]:
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.INVALID_CHECKSUM,
                "Dígitos verificadores do CNPJ não conferem.",
                "CNPJ checksum digits do not match.",
            ),
        )

    return ValidationResult(
        valid=True,
        raw=raw,
        formatted=_format_cnpj(canon),
        extras={"format": cnpj_format},
    )
