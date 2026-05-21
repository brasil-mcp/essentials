"""Validator de Título de Eleitor brasileiro (12 dígitos, módulo 11 com UF embutida)."""

from __future__ import annotations

import re

from brasil_mcp.core.errors import ErrorCode, ErrorObj
from brasil_mcp.core.models import ValidationResult

_MASK_RE = re.compile(r"[^\d]")
_ALLOWED_CHARS_RE = re.compile(r"[^\d\s]")

# UF code (2-digit) → UF abbreviation. Code 28 is "Exterior" (votantes no estrangeiro).
_UF_MAP: dict[str, str] = {
    "01": "SP", "02": "MG", "03": "RJ", "04": "RS", "05": "BA", "06": "PR",
    "07": "CE", "08": "PE", "09": "SC", "10": "GO", "11": "MA", "12": "PB",
    "13": "PA", "14": "ES", "15": "PI", "16": "RN", "17": "AL", "18": "MT",
    "19": "MS", "20": "DF", "21": "SE", "22": "AM", "23": "RO", "24": "AC",
    "25": "AP", "26": "RR", "27": "TO", "28": "Exterior",
}

# UFs where the mod-11 exception (rem >= 10) collapses to 1 (not 0).
_SP_MG_EXCEPTION = {"01", "02"}


def _format_titulo(digits: str) -> str:
    # Título de Eleitor has no canonical mask — return 12 digits.
    return digits


def _calc_dv(values: str, weights: list[int], uf: str) -> int:
    """Compute a mod-11 DV with the SP/MG exception:
    when remainder is 10, the DV is 0 — except for SP (01) and MG (02), where it becomes 1.
    """
    total = sum(int(c) * w for c, w in zip(values, weights, strict=True))
    rem = total % 11
    if rem >= 10:
        return 1 if uf in _SP_MG_EXCEPTION else 0
    return rem


def validate_titulo_eleitor(value: str) -> ValidationResult:
    raw = value or ""
    if not raw.strip():
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.EMPTY_INPUT,
                "Título de Eleitor não pode ser vazio.",
                "Voter ID cannot be empty.",
            ),
        )

    if _ALLOWED_CHARS_RE.search(raw):
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.INVALID_CHARACTER,
                "Título de Eleitor deve conter apenas dígitos.",
                "Voter ID must contain only digits.",
            ),
        )

    digits = _MASK_RE.sub("", raw)

    if len(digits) != 12:
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.INVALID_LENGTH,
                f"Título de Eleitor deve ter 12 dígitos; recebido {len(digits)}.",
                f"Voter ID must have 12 digits; received {len(digits)}.",
                suggestion="Verifique se o número não está truncado.",
            ),
        )

    if len(set(digits)) == 1:
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.REPEATED_DIGITS,
                "Título de Eleitor com todos os dígitos iguais é inválido.",
                "Voter ID with all repeated digits is invalid.",
            ),
        )

    # Positions: 0..7 = sequence, 8..9 = UF, 10 = DV1, 11 = DV2.
    seq = digits[:8]
    uf = digits[8:10]
    given_dv1 = int(digits[10])
    given_dv2 = int(digits[11])

    if uf not in _UF_MAP:
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.INVALID_FORMAT,
                f"Código de UF '{uf}' não reconhecido no Título de Eleitor.",
                f"Unknown UF code '{uf}' in voter ID.",
            ),
        )

    dv1 = _calc_dv(seq, [2, 3, 4, 5, 6, 7, 8, 9], uf)
    # DV2 uses UF chars + DV1 with weights [7, 8, 9].
    dv2 = _calc_dv(uf + str(dv1), [7, 8, 9], uf)

    if dv1 != given_dv1 or dv2 != given_dv2:
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.INVALID_CHECKSUM,
                "Dígitos verificadores do Título de Eleitor não conferem.",
                "Voter ID checksum digits do not match.",
            ),
        )

    return ValidationResult(
        valid=True,
        raw=raw,
        formatted=_format_titulo(digits),
        extras={"uf": _UF_MAP[uf]},
    )
