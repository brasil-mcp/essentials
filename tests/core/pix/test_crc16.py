"""Tests for CRC16-CCITT-FALSE."""

from __future__ import annotations

from brasil_mcp.core.pix.crc16 import crc16_ccitt_false, crc16_hex


def test_crc16_standard_vector() -> None:
    # Standard CRC16-CCITT-FALSE check vector.
    assert crc16_ccitt_false(b"123456789") == 0x29B1


def test_crc16_hex_format() -> None:
    out = crc16_hex("123456789")
    assert out == "29B1"
    assert len(out) == 4
    assert out == out.upper()


def test_crc16_empty_bytes() -> None:
    # Initial CRC value is 0xFFFF.
    assert crc16_ccitt_false(b"") == 0xFFFF


def test_crc16_hex_pads_to_4_chars() -> None:
    # Some inputs produce CRC < 0x1000 — ensure left-padded hex.
    out = crc16_hex("A")
    assert len(out) == 4
    assert all(c in "0123456789ABCDEF" for c in out)
