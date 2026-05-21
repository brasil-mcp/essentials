"""CRC16-CCITT-FALSE (poly 0x1021, init 0xFFFF) — usado em PIX BR Code."""

from __future__ import annotations


def crc16_ccitt_false(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if (crc & 0x8000) else (crc << 1) & 0xFFFF
    return crc


def crc16_hex(payload: str) -> str:
    """Returns the 4-char uppercase hex CRC for a PIX BR Code payload (excluding the CRC field)."""
    return f"{crc16_ccitt_false(payload.encode('utf-8')):04X}"
