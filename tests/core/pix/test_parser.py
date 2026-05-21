"""Tests for parse_pix_brcode + generate_pix_brcode."""

from __future__ import annotations

import base64

from brasil_mcp.core.errors import ErrorCode
from brasil_mcp.core.pix.parser import (
    _classify_chave,
    generate_pix_brcode,
    parse_pix_brcode,
)


def test_generate_then_parse_roundtrip() -> None:
    out = generate_pix_brcode(
        chave="joao@example.com",
        nome_beneficiario="JOAO DA SILVA",
        cidade="SAO PAULO",
        valor=12345,
        txid="PEDIDO12345",
        descricao="Pagamento NF",
    )
    assert out["error"] is None
    assert out["brcode"] is not None
    parsed = parse_pix_brcode(out["brcode"])
    assert parsed.valid is True
    assert parsed.error is None
    assert parsed.extras["chave"] == "joao@example.com"
    assert parsed.extras["tipo_chave"] == "email"
    assert parsed.extras["beneficiario"] == "JOAO DA SILVA"
    assert parsed.extras["cidade"] == "SAO PAULO"
    assert parsed.extras["valor"] == 12345
    assert parsed.extras["moeda"] == "BRL"
    assert parsed.extras["txid"] == "PEDIDO12345"
    assert parsed.extras["descricao"] == "Pagamento NF"
    assert parsed.extras["dinamico"] is False
    assert parsed.extras["url_provedor"] is None


def test_generate_with_email_key() -> None:
    out = generate_pix_brcode(
        chave="user@example.com",
        nome_beneficiario="JOAO",
        cidade="SAO PAULO",
    )
    assert out["error"] is None
    parsed = parse_pix_brcode(out["brcode"])
    assert parsed.valid is True
    assert parsed.extras["tipo_chave"] == "email"
    assert parsed.extras["valor"] is None


def test_generate_with_cpf_key() -> None:
    out = generate_pix_brcode(
        chave="12345678901",
        nome_beneficiario="JOAO",
        cidade="SAO PAULO",
    )
    assert out["error"] is None
    parsed = parse_pix_brcode(out["brcode"])
    assert parsed.valid is True
    assert parsed.extras["tipo_chave"] == "cpf"


def test_generate_qr_png() -> None:
    out = generate_pix_brcode(
        chave="user@example.com",
        nome_beneficiario="JOAO",
        cidade="SAO PAULO",
        qr_format="png",
    )
    assert out["error"] is None
    assert out["qr_png_base64"] is not None
    assert out["qr_svg"] is None
    # Validate base64 decodes to PNG signature.
    decoded = base64.b64decode(out["qr_png_base64"])
    assert decoded.startswith(b"\x89PNG\r\n\x1a\n")


def test_generate_qr_svg() -> None:
    out = generate_pix_brcode(
        chave="user@example.com",
        nome_beneficiario="JOAO",
        cidade="SAO PAULO",
        qr_format="svg",
    )
    assert out["error"] is None
    assert out["qr_svg"] is not None
    assert out["qr_png_base64"] is None
    assert "<svg" in out["qr_svg"]


def test_generate_qr_both() -> None:
    out = generate_pix_brcode(
        chave="user@example.com",
        nome_beneficiario="JOAO",
        cidade="SAO PAULO",
        qr_format="both",
    )
    assert out["error"] is None
    assert out["qr_png_base64"] is not None
    assert out["qr_svg"] is not None


def test_generate_invalid_qr_format() -> None:
    out = generate_pix_brcode(
        chave="user@example.com",
        nome_beneficiario="JOAO",
        cidade="SAO PAULO",
        qr_format="jpeg",
    )
    assert out["error"] is not None
    assert out["error"]["code"] == ErrorCode.INVALID_FORMAT
    assert out["brcode"] is None


def test_generate_missing_chave() -> None:
    out = generate_pix_brcode(
        chave="",
        nome_beneficiario="JOAO",
        cidade="SAO PAULO",
    )
    assert out["error"] is not None
    assert out["error"]["code"] == ErrorCode.MISSING_REQUIRED_FIELD


def test_generate_missing_chave_whitespace_only() -> None:
    out = generate_pix_brcode(
        chave="   ",
        nome_beneficiario="JOAO",
        cidade="SAO PAULO",
    )
    assert out["error"] is not None
    assert out["error"]["code"] == ErrorCode.MISSING_REQUIRED_FIELD


def test_classify_keys() -> None:
    assert _classify_chave("joao@example.com") == "email"
    assert _classify_chave("+5511999999999") == "telefone"
    assert _classify_chave("12345678901") == "cpf"
    assert _classify_chave("12345678000199") == "cnpj"
    assert _classify_chave("550e8400-e29b-41d4-a716-446655440000") == "aleatoria"
    assert _classify_chave("random-string-xyz") == "aleatoria"


def test_parse_invalid_crc() -> None:
    out = generate_pix_brcode(
        chave="user@example.com",
        nome_beneficiario="JOAO",
        cidade="SAO PAULO",
    )
    brcode = out["brcode"]
    assert brcode is not None
    # Corrupt the last 4 chars (CRC).
    corrupted = brcode[:-4] + ("FFFF" if brcode[-4:] != "FFFF" else "0000")
    parsed = parse_pix_brcode(corrupted)
    assert parsed.valid is False
    assert parsed.error is not None
    assert parsed.error.code == ErrorCode.INVALID_CHECKSUM


def test_parse_empty_input() -> None:
    parsed = parse_pix_brcode("")
    assert parsed.valid is False
    assert parsed.error is not None
    assert parsed.error.code == ErrorCode.EMPTY_INPUT

    parsed2 = parse_pix_brcode("   ")
    assert parsed2.valid is False
    assert parsed2.error is not None
    assert parsed2.error.code == ErrorCode.EMPTY_INPUT


def test_parse_malformed() -> None:
    parsed = parse_pix_brcode("this is not a pix brcode")
    assert parsed.valid is False
    assert parsed.error is not None
    assert parsed.error.code in {ErrorCode.INVALID_FORMAT, ErrorCode.UNSUPPORTED_FORMAT}


def test_strips_accents_uppercase() -> None:
    out = generate_pix_brcode(
        chave="user@example.com",
        nome_beneficiario="João da Silva",
        cidade="São Paulo",
    )
    assert out["error"] is None
    parsed = parse_pix_brcode(out["brcode"])
    assert parsed.valid is True
    assert parsed.extras["beneficiario"] == "JOAO DA SILVA"
    assert parsed.extras["cidade"] == "SAO PAULO"


def test_truncates_long_name() -> None:
    long_name = "A" * 50
    out = generate_pix_brcode(
        chave="user@example.com",
        nome_beneficiario=long_name,
        cidade="SAO PAULO",
    )
    assert out["error"] is None
    parsed = parse_pix_brcode(out["brcode"])
    assert parsed.valid is True
    assert len(parsed.extras["beneficiario"]) == 25
    assert parsed.extras["beneficiario"] == "A" * 25


def test_truncates_long_city() -> None:
    out = generate_pix_brcode(
        chave="user@example.com",
        nome_beneficiario="JOAO",
        cidade="C" * 30,
    )
    assert out["error"] is None
    parsed = parse_pix_brcode(out["brcode"])
    assert parsed.valid is True
    assert len(parsed.extras["cidade"]) == 15


def test_generate_no_amount_omits_tag_54() -> None:
    out = generate_pix_brcode(
        chave="user@example.com",
        nome_beneficiario="JOAO",
        cidade="SAO PAULO",
    )
    assert out["error"] is None
    # Tag 54 should not be present when no valor specified.
    assert "5404" not in out["brcode"]
    parsed = parse_pix_brcode(out["brcode"])
    assert parsed.extras["valor"] is None


def test_generate_zero_amount_omits_tag_54() -> None:
    out = generate_pix_brcode(
        chave="user@example.com",
        nome_beneficiario="JOAO",
        cidade="SAO PAULO",
        valor=0,
    )
    assert out["error"] is None
    parsed = parse_pix_brcode(out["brcode"])
    assert parsed.extras["valor"] is None


def test_parse_txid_placeholder_treated_as_none() -> None:
    out = generate_pix_brcode(
        chave="user@example.com",
        nome_beneficiario="JOAO",
        cidade="SAO PAULO",
    )
    parsed = parse_pix_brcode(out["brcode"])
    assert parsed.valid is True
    assert parsed.extras["txid"] is None


def test_amount_format_two_decimals() -> None:
    out = generate_pix_brcode(
        chave="user@example.com",
        nome_beneficiario="JOAO",
        cidade="SAO PAULO",
        valor=100,  # R$ 1,00
    )
    assert out["error"] is None
    parsed = parse_pix_brcode(out["brcode"])
    assert parsed.extras["valor"] == 100
