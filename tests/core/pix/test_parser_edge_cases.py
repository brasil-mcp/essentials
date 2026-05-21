"""Edge-case tests for parse_pix_brcode + generate_pix_brcode.

Each test maps to one (or a few) missing-line/branch in `core/pix/parser.py`.
"""

from __future__ import annotations

from brasil_mcp.core.errors import ErrorCode
from brasil_mcp.core.pix.brcode import TLV, encode_tlvs
from brasil_mcp.core.pix.crc16 import crc16_hex
from brasil_mcp.core.pix.parser import (
    _classify_chave,
    generate_pix_brcode,
    parse_pix_brcode,
)


def _wrap_with_crc(body: str) -> str:
    """Append the proper CRC tail to a TLV body so parse_pix_brcode passes the
    CRC check and we can target downstream parse logic.
    """
    crc_input = body + "6304"
    return crc_input + crc16_hex(crc_input)


# ---------------------------------------------------------------------------
# _classify_chave branches
# ---------------------------------------------------------------------------


def test_classify_chave_empty_returns_aleatoria() -> None:
    """Line 65: empty chave classifies as 'aleatoria' (random)."""
    assert _classify_chave("") == "aleatoria"


def test_classify_chave_plus_prefix_too_few_digits() -> None:
    """Branch 70->72: starts with '+' but digits count < 12, falls through."""
    assert _classify_chave("+55") == "aleatoria"


def test_classify_chave_digits_only_wrong_length() -> None:
    """Branch 75->77: digits-only but length != 11/14 falls through."""
    assert _classify_chave("12345") == "aleatoria"


# ---------------------------------------------------------------------------
# parse_pix_brcode error paths
# ---------------------------------------------------------------------------


def test_parse_pix_invalid_payload_format() -> None:
    """Line 145: payload format indicator ('00' tag) missing or wrong value."""
    # Build a TLV body with no tag 00 (replace it with another tag that has wrong format).
    ma_value = encode_tlvs([TLV("00", "BR.GOV.BCB.PIX"), TLV("01", "x@y.com")])
    # tag 00 set to '99' (invalid)
    body = encode_tlvs(
        [
            TLV("00", "99"),
            TLV("26", ma_value),
            TLV("52", "0000"),
            TLV("53", "986"),
            TLV("58", "BR"),
            TLV("59", "JOAO"),
            TLV("60", "SP"),
        ]
    )
    payload = _wrap_with_crc(body)
    result = parse_pix_brcode(payload)
    assert result.valid is False
    assert result.error is not None
    assert result.error.code == ErrorCode.UNSUPPORTED_FORMAT


def test_parse_pix_missing_merchant_account_tag_26() -> None:
    """Line 157: tag 26 (merchant account info) missing."""
    body = encode_tlvs(
        [
            TLV("00", "01"),
            TLV("52", "0000"),
            TLV("53", "986"),
            TLV("58", "BR"),
            TLV("59", "JOAO"),
            TLV("60", "SP"),
        ]
    )
    payload = _wrap_with_crc(body)
    result = parse_pix_brcode(payload)
    assert result.valid is False
    assert result.error is not None
    assert result.error.code == ErrorCode.UNSUPPORTED_FORMAT
    assert "26" in result.error.message_pt


def test_parse_pix_tag_26_malformed_sub_tlvs() -> None:
    """Lines 169-170: tag 26 sub-TLV decode raises ValueError → INVALID_FORMAT.

    We craft a tag 26 whose interior is not a valid TLV stream by giving it an
    odd-length value that, when decode_tlv tries to read the 2-char length
    prefix, blows up with ValueError on `int(...)`.
    """
    # The interior must NOT be empty and must NOT parse cleanly.
    # decode_tlv reads 2-char tag + 2-char length. If the length is "XX" it
    # raises ValueError on int().
    bad_ma = "00XXgarbage"  # "00" tag, "XX" length (not numeric)
    body = encode_tlvs(
        [
            TLV("00", "01"),
            TLV("26", bad_ma),
            TLV("52", "0000"),
            TLV("53", "986"),
            TLV("58", "BR"),
            TLV("59", "JOAO"),
            TLV("60", "SP"),
        ]
    )
    payload = _wrap_with_crc(body)
    result = parse_pix_brcode(payload)
    assert result.valid is False
    assert result.error is not None
    assert result.error.code == ErrorCode.INVALID_FORMAT


def test_parse_pix_gui_not_pix() -> None:
    """Line 182: GUI inside tag 26 isn't BR.GOV.BCB.PIX → UNSUPPORTED_FORMAT."""
    ma_value = encode_tlvs([TLV("00", "EVIL.CORP.GUI"), TLV("01", "x@y.com")])
    body = encode_tlvs(
        [
            TLV("00", "01"),
            TLV("26", ma_value),
            TLV("52", "0000"),
            TLV("53", "986"),
            TLV("58", "BR"),
            TLV("59", "JOAO"),
            TLV("60", "SP"),
        ]
    )
    payload = _wrap_with_crc(body)
    result = parse_pix_brcode(payload)
    assert result.valid is False
    assert result.error is not None
    assert result.error.code == ErrorCode.UNSUPPORTED_FORMAT


def test_parse_pix_invalid_amount_in_tag_54() -> None:
    """Lines 206-207: tag 54 (amount) is non-numeric → INVALID_FORMAT."""
    ma_value = encode_tlvs([TLV("00", "BR.GOV.BCB.PIX"), TLV("01", "user@example.com")])
    body = encode_tlvs(
        [
            TLV("00", "01"),
            TLV("26", ma_value),
            TLV("52", "0000"),
            TLV("53", "986"),
            TLV("54", "NOTANUMBER"),  # bad amount
            TLV("58", "BR"),
            TLV("59", "JOAO"),
            TLV("60", "SP"),
        ]
    )
    payload = _wrap_with_crc(body)
    result = parse_pix_brcode(payload)
    assert result.valid is False
    assert result.error is not None
    assert result.error.code == ErrorCode.INVALID_FORMAT
    assert "54" in result.error.message_pt


def test_parse_pix_additional_data_malformed_sub_tlvs() -> None:
    """Lines 226-227: tag 62 sub-TLV decode raises → ad_subs becomes {}.

    This branch is the exception swallow inside parse_pix_brcode for the
    additional-data block. Parsing should still succeed (txid just stays None).
    """
    ma_value = encode_tlvs([TLV("00", "BR.GOV.BCB.PIX"), TLV("01", "user@example.com")])
    bad_ad = "05ZZbad"  # length "ZZ" is not an int → ValueError
    body = encode_tlvs(
        [
            TLV("00", "01"),
            TLV("26", ma_value),
            TLV("52", "0000"),
            TLV("53", "986"),
            TLV("58", "BR"),
            TLV("59", "JOAO"),
            TLV("60", "SP"),
            TLV("62", bad_ad),
        ]
    )
    payload = _wrap_with_crc(body)
    result = parse_pix_brcode(payload)
    # Top-level should still be valid — the swallowed exception sets ad_subs = {}.
    assert result.valid is True
    assert result.extras["txid"] is None


def test_parse_pix_top_level_tlv_decode_failure() -> None:
    """Lines 132-133: top-level decode_tlv raises after CRC passes.

    We need a payload that:
    1. ends in 6304XXXX with a valid CRC,
    2. has body whose first TLV cannot be parsed.

    We achieve this by giving an explicit body of "00XXgarbage..." then
    appending a properly-computed CRC for *exactly that body*.
    """
    body = "00XXgarbagecontent"
    payload = _wrap_with_crc(body)
    result = parse_pix_brcode(payload)
    assert result.valid is False
    assert result.error is not None
    assert result.error.code == ErrorCode.INVALID_FORMAT
    assert "TLV" in result.error.message_en


def test_parse_pix_dynamic_with_url_provedor() -> None:
    """Cover the dynamic=True branch (sub-TLV 25 in tag 26)."""
    ma_value = encode_tlvs(
        [
            TLV("00", "BR.GOV.BCB.PIX"),
            TLV("25", "https://bank.example.com/pix/abc"),
        ]
    )
    body = encode_tlvs(
        [
            TLV("00", "01"),
            TLV("26", ma_value),
            TLV("52", "0000"),
            TLV("53", "986"),
            TLV("58", "BR"),
            TLV("59", "JOAO"),
            TLV("60", "SP"),
        ]
    )
    payload = _wrap_with_crc(body)
    result = parse_pix_brcode(payload)
    assert result.valid is True
    assert result.extras["dinamico"] is True
    assert result.extras["url_provedor"] == "https://bank.example.com/pix/abc"
    assert result.extras["chave"] == ""  # no chave when dynamic


def test_parse_pix_with_real_txid() -> None:
    """Cover the txid-set branch (vs placeholder '***')."""
    out = generate_pix_brcode(
        chave="user@example.com",
        nome_beneficiario="JOAO",
        cidade="SP",
        txid="REALTXID",
    )
    parsed = parse_pix_brcode(out["brcode"])
    assert parsed.extras["txid"] == "REALTXID"


def test_parse_pix_non_brl_currency_preserved() -> None:
    """Cover the `moeda != BRL` branch in parser (moeda_code preserved as-is)."""
    ma_value = encode_tlvs([TLV("00", "BR.GOV.BCB.PIX"), TLV("01", "user@example.com")])
    body = encode_tlvs(
        [
            TLV("00", "01"),
            TLV("26", ma_value),
            TLV("52", "0000"),
            TLV("53", "840"),  # USD
            TLV("58", "BR"),
            TLV("59", "JOAO"),
            TLV("60", "SP"),
        ]
    )
    payload = _wrap_with_crc(body)
    result = parse_pix_brcode(payload)
    assert result.valid is True
    assert result.extras["moeda"] == "840"
