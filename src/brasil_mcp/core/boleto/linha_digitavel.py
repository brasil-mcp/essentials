"""Helpers de normalização, dígito verificador e conversão entre formatos
de linha digitável / código de barras (FEBRABAN, bancário 47/44)."""

from __future__ import annotations

import re

_NON_DIGIT_RE = re.compile(r"\D")


def normalize(s: str) -> str:
    """Remove todos os caracteres não-dígitos."""
    return _NON_DIGIT_RE.sub("", s or "")


def is_arrecadacao(digits: str) -> bool:
    """True se a string começa com '8' (boleto de arrecadação/concessionária/tributo)."""
    return bool(digits) and digits[0] == "8"


def dv_mod10(digits: str) -> int:
    """Cálculo de DV módulo 10 (FEBRABAN).

    Da direita para a esquerda, multiplica cada dígito pelos pesos 2,1,2,1,...
    Se o produto for > 9, soma os dígitos do produto (ex.: 14 -> 1+4 = 5).
    DV = (10 - (sum % 10)) % 10.
    """
    total = 0
    # right-to-left, weights alternate 2,1,2,1,...
    for i, ch in enumerate(reversed(digits)):
        weight = 2 if i % 2 == 0 else 1
        product = int(ch) * weight
        if product > 9:
            product = (product // 10) + (product % 10)
        total += product
    return (10 - (total % 10)) % 10


def dv_mod11_bancario(digits: str) -> int:
    """Cálculo de DV módulo 11 (FEBRABAN bancário, DV geral do código de barras).

    Pesos cíclicos 2..9 da direita para a esquerda.
    DV = 11 - (sum % 11).
    Se DV ∈ {0, 10, 11}, retorna 1 (regra FEBRABAN para DV geral).
    """
    total = 0
    weight = 2
    for ch in reversed(digits):
        total += int(ch) * weight
        weight += 1
        if weight > 9:
            weight = 2
    dv = 11 - (total % 11)
    if dv in (0, 10, 11):
        return 1
    return dv


def linha_to_barcode_bancario(linha47: str) -> str:
    """Converte linha digitável de 47 dígitos no código de barras de 44 dígitos.

    Layout (índices zero-based):
      barcode[0:4]   = linha[0:4]      # banco + moeda
      barcode[4:5]   = linha[32:33]    # DV geral
      barcode[5:9]   = linha[33:37]    # fator vencimento
      barcode[9:19]  = linha[37:47]    # valor
      barcode[19:24] = linha[4:9]      # campo 1 (5 dígitos sem o DV)
      barcode[24:34] = linha[10:20]    # campo 2 (10 dígitos sem o DV)
      barcode[34:44] = linha[21:31]    # campo 3 (10 dígitos sem o DV)
    """
    if len(linha47) != 47:
        raise ValueError(f"linha digitável bancária deve ter 47 dígitos; recebido {len(linha47)}")
    parts = [
        linha47[0:4],
        linha47[32:33],
        linha47[33:37],
        linha47[37:47],
        linha47[4:9],
        linha47[10:20],
        linha47[21:31],
    ]
    return "".join(parts)


def barcode_to_linha_bancario(barcode44: str) -> str:
    """Inverso de :func:`linha_to_barcode_bancario`.

    Reconstrói os 47 dígitos a partir do código de barras 44, recalculando
    os DVs módulo 10 dos campos 1, 2 e 3.
    """
    if len(barcode44) != 44:
        raise ValueError(
            f"código de barras bancário deve ter 44 dígitos; recebido {len(barcode44)}"
        )

    banco_moeda = barcode44[0:4]
    dv_geral = barcode44[4:5]
    fator_valor = barcode44[5:19]  # 4 + 10
    campo1_data = barcode44[19:24]  # 5 dígitos
    campo2_data = barcode44[24:34]  # 10 dígitos
    campo3_data = barcode44[34:44]  # 10 dígitos

    campo1 = banco_moeda + campo1_data
    dv1 = dv_mod10(campo1)
    dv2 = dv_mod10(campo2_data)
    dv3 = dv_mod10(campo3_data)

    return (
        f"{banco_moeda}{campo1_data}{dv1}"
        f"{campo2_data}{dv2}"
        f"{campo3_data}{dv3}"
        f"{dv_geral}{fator_valor}"
    )
