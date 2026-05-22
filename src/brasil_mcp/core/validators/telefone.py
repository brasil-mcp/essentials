"""Validator/formatter de telefone brasileiro (fixo e celular).

Aceita inputs com qualquer mascarado: `(11) 98765-4321`, `+5511987654321`,
`11987654321`, `11 9 8765 4321`. Strip de qualquer não-dígito/+ pra normalizar.

Reconhece:
- Celular: 11 dígitos com DDD + 9 + 8 dígitos (segundo dígito após DDD = 9).
- Fixo: 10 dígitos com DDD + 8 dígitos (segundo dígito após DDD em 2-5).
- Internacional: prefixo `+55` opcional.

Outputs três representações:
- `formatted`: `(11) 98765-4321` (celular) ou `(11) 3456-7890` (fixo).
- `formatted_international`: `+55 11 98765-4321`.
- `e164`: `+5511987654321` (E.164 puro, sem espaços).
"""

from __future__ import annotations

import re

from brasil_mcp.core.errors import ErrorCode, ErrorObj
from brasil_mcp.core.models import ValidationResult

_NON_DIGIT_PLUS = re.compile(r"[^\d+]")

# DDDs brasileiros conhecidos (lista oficial Anatel). Codes não-atribuídos
# (ex 20, 23, 25, 26, 29, 30, 36, 39, 40, 50, 52, 56, 57, 58, 59, 60, 70,
# 72, 76, 78, 80, 90) são rejeitados.
DDDS_VALIDOS = frozenset(
    {
        "11",
        "12",
        "13",
        "14",
        "15",
        "16",
        "17",
        "18",
        "19",
        "21",
        "22",
        "24",
        "27",
        "28",
        "31",
        "32",
        "33",
        "34",
        "35",
        "37",
        "38",
        "41",
        "42",
        "43",
        "44",
        "45",
        "46",
        "47",
        "48",
        "49",
        "51",
        "53",
        "54",
        "55",
        "61",
        "62",
        "63",
        "64",
        "65",
        "66",
        "67",
        "68",
        "69",
        "71",
        "73",
        "74",
        "75",
        "77",
        "79",
        "81",
        "82",
        "83",
        "84",
        "85",
        "86",
        "87",
        "88",
        "89",
        "91",
        "92",
        "93",
        "94",
        "95",
        "96",
        "97",
        "98",
        "99",
    }
)


def _strip_to_digits_and_plus(value: str) -> str:
    return _NON_DIGIT_PLUS.sub("", value or "")


def _err(value: str, code: ErrorCode, pt: str, en: str) -> ValidationResult:
    return ValidationResult(valid=False, raw=value, error=ErrorObj(code, pt, en))


def validate_telefone(value: str) -> ValidationResult:
    """Valida + normaliza telefone brasileiro.

    Returns ValidationResult with extras:
        { formatted, formatted_international, e164, ddd, tipo:
          "celular" | "fixo" }
    """
    raw = value or ""
    if not raw.strip():
        return _err(
            raw, ErrorCode.EMPTY_INPUT, "Telefone não pode ser vazio.", "Telefone cannot be empty."
        )

    stripped = _strip_to_digits_and_plus(raw)

    # Strip leading +55 country code if present
    if stripped.startswith("+55"):
        stripped = stripped[3:]
    elif stripped.startswith("55") and len(stripped) in (12, 13):
        stripped = stripped[2:]
    elif stripped.startswith("+"):
        # Has a + but not +55 → not BR
        return _err(
            raw,
            ErrorCode.UNSUPPORTED_FORMAT,
            "Apenas códigos brasileiros (+55) são suportados.",
            "Only Brazilian country code (+55) is supported.",
        )

    # Now stripped should be all digits, length 10 or 11
    if not stripped.isdigit():
        return _err(
            raw,
            ErrorCode.INVALID_CHARACTER,
            "Telefone deve conter apenas dígitos e máscara opcional.",
            "Telefone must contain only digits and optional mask.",
        )

    if len(stripped) not in (10, 11):
        return _err(
            raw,
            ErrorCode.INVALID_LENGTH,
            f"Telefone brasileiro deve ter 10 (fixo) ou 11 (celular) dígitos com DDD; recebido {len(stripped)}.",
            f"Brazilian telefone must have 10 (fixo) or 11 (celular) digits with DDD; got {len(stripped)}.",
        )

    ddd = stripped[:2]
    if ddd not in DDDS_VALIDOS:
        return _err(
            raw,
            ErrorCode.INVALID_FORMAT,
            f"DDD '{ddd}' não é um código brasileiro válido.",
            f"DDD '{ddd}' is not a valid Brazilian code.",
        )

    rest = stripped[2:]

    if len(stripped) == 11:
        # Celular: segundo dígito após DDD deve ser 9
        if rest[0] != "9":
            return _err(
                raw,
                ErrorCode.INVALID_FORMAT,
                "Celular brasileiro de 11 dígitos deve começar com 9 após o DDD.",
                "11-digit Brazilian celular must start with 9 after the DDD.",
            )
        tipo = "celular"
        formatted = f"({ddd}) {rest[:5]}-{rest[5:]}"
    else:
        # Fixo: primeiro dígito após DDD em 2-5 (atribuído pela Anatel pra fixos).
        if rest[0] not in "2345":
            return _err(
                raw,
                ErrorCode.INVALID_FORMAT,
                "Telefone fixo brasileiro de 10 dígitos deve começar com 2-5 após o DDD.",
                "10-digit Brazilian fixo telefone must start with 2-5 after the DDD.",
            )
        tipo = "fixo"
        formatted = f"({ddd}) {rest[:4]}-{rest[4:]}"

    e164 = f"+55{stripped}"
    if tipo == "celular":
        formatted_intl = f"+55 {ddd} {rest[:5]}-{rest[5:]}"
    else:
        formatted_intl = f"+55 {ddd} {rest[:4]}-{rest[4:]}"

    return ValidationResult(
        valid=True,
        raw=raw,
        formatted=formatted,
        extras={
            "formatted_international": formatted_intl,
            "e164": e164,
            "ddd": ddd,
            "tipo": tipo,
        },
    )
