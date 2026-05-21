"""Validator de cartão de crédito (12-19 dígitos, Luhn + detecção de bandeira)."""

from __future__ import annotations

import re

from brasil_mcp.core.errors import ErrorCode, ErrorObj
from brasil_mcp.core.models import ValidationResult

_MASK_RE = re.compile(r"[^\d]")
# Credit cards are commonly entered with spaces; allow digits + spaces only.
_ALLOWED_CHARS_RE = re.compile(r"[^\d ]")

# Brazilian-specific Elo BIN prefixes.
_ELO_PREFIXES = (
    "4011",
    "4312",
    "4389",
    "4514",
    "4573",
    "5041",
    "5066",
    "5067",
    "6362",
    "6504",
    "6505",
    "6516",
    "6550",
)

# Brazilian-specific Hipercard BIN prefixes.
_HIPERCARD_PREFIXES = (
    "384100",
    "384140",
    "384160",
    "606282",
    "637095",
    "637568",
    "637599",
    "637609",
    "637612",
)


def _format_card(digits: str) -> str:
    # Groups of 4, space-separated.
    return " ".join(digits[i : i + 4] for i in range(0, len(digits), 4))


def _luhn_valid(digits: str) -> bool:
    total = 0
    for i, c in enumerate(reversed(digits)):
        d = int(c)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def _detect_brand(digits: str) -> str | None:
    n = len(digits)

    # amex: 34/37, length 15.
    if n == 15 and digits[:2] in ("34", "37"):
        return "amex"

    # visa: starts with 4, length 13/16/19.
    if digits[0] == "4" and n in (13, 16, 19):
        # Elo (BR-specific) overrides generic visa when prefix matches.
        if any(digits.startswith(p) for p in _ELO_PREFIXES):
            return "elo"
        return "visa"

    # mastercard: 51-55 OR 2221-2720, length 16.
    if n == 16:
        if digits[:2] in {"51", "52", "53", "54", "55"}:
            return "mastercard"
        first4 = int(digits[:4])
        if 2221 <= first4 <= 2720:
            return "mastercard"

    # elo: any of the BR-specific prefixes.
    if any(digits.startswith(p) for p in _ELO_PREFIXES):
        return "elo"

    # hipercard: BR-specific prefixes.
    if any(digits.startswith(p) for p in _HIPERCARD_PREFIXES):
        return "hipercard"

    # discover: 6011 or 65, length 16.
    if n == 16 and (digits.startswith("6011") or digits.startswith("65")):
        return "discover"

    # diners: 300-305, 36, 38, length 14.
    if n == 14:
        if digits[:3] in {"300", "301", "302", "303", "304", "305"}:
            return "diners"
        if digits[:2] in {"36", "38"}:
            return "diners"

    # jcb: 352-358, length 16.
    if n == 16 and digits[:3] in {"352", "353", "354", "355", "356", "357", "358"}:
        return "jcb"

    return None


def validate_credit_card(value: str) -> ValidationResult:
    raw = value or ""
    if not raw.strip():
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.EMPTY_INPUT,
                "Número do cartão não pode ser vazio.",
                "Card number cannot be empty.",
            ),
        )

    if _ALLOWED_CHARS_RE.search(raw):
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.INVALID_CHARACTER,
                "Número do cartão deve conter apenas dígitos e espaços.",
                "Card number must contain only digits and spaces.",
            ),
        )

    digits = _MASK_RE.sub("", raw)

    if not (12 <= len(digits) <= 19):
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.INVALID_LENGTH,
                f"Número do cartão deve ter de 12 a 19 dígitos; recebido {len(digits)}.",
                f"Card number must have 12 to 19 digits; received {len(digits)}.",
            ),
        )

    if not _luhn_valid(digits):
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.INVALID_CHECKSUM,
                "Checksum de Luhn do cartão não confere.",
                "Card Luhn checksum does not match.",
            ),
        )

    brand = _detect_brand(digits)
    return ValidationResult(
        valid=True,
        raw=raw,
        formatted=_format_card(digits),
        extras={"brand": brand},
    )
