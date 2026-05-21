"""Tests for EMV TLV codec."""

from __future__ import annotations

from brasil_mcp.core.pix.brcode import TLV, decode_tlv, encode_tlvs


def test_tlv_encode_basic() -> None:
    assert TLV("00", "01").encode() == "000201"
    assert TLV("58", "BR").encode() == "5802BR"


def test_tlv_encode_longer_value() -> None:
    # length is zero-padded 2-digit
    assert TLV("59", "JOAO DA SILVA").encode() == f"5913{'JOAO DA SILVA'}"


def test_decode_tlv_simple() -> None:
    payload = "000201" + "5802BR"
    out = decode_tlv(payload)
    assert out == {"00": "01", "58": "BR"}


def test_decode_tlv_with_range() -> None:
    payload = "AA0102" + "BB0205"
    out = decode_tlv(payload, start=6)
    assert out == {"BB": "05"}


def test_encode_decode_roundtrip() -> None:
    tlvs = [
        TLV("00", "01"),
        TLV("52", "0000"),
        TLV("53", "986"),
        TLV("58", "BR"),
        TLV("59", "JOAO DA SILVA"),
        TLV("60", "SAO PAULO"),
    ]
    encoded = encode_tlvs(tlvs)
    decoded = decode_tlv(encoded)
    assert decoded == {
        "00": "01",
        "52": "0000",
        "53": "986",
        "58": "BR",
        "59": "JOAO DA SILVA",
        "60": "SAO PAULO",
    }


def test_decode_tlv_empty_string() -> None:
    assert decode_tlv("") == {}


def test_decode_tlv_truncated_returns_partial() -> None:
    # Truncated trailing TLV should be skipped, but earlier ones returned.
    payload = "000201" + "AB"  # second tag has no length
    out = decode_tlv(payload)
    assert out == {"00": "01"}
