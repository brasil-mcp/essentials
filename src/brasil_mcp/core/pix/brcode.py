"""EMV TLV encoder/decoder pra PIX BR Code."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TLV:
    tag: str
    value: str

    def encode(self) -> str:
        return f"{self.tag}{len(self.value):02d}{self.value}"


def decode_tlv(payload: str, start: int = 0, end: int | None = None) -> dict[str, str]:
    """Decode TLVs at given range. Returns dict of tag → raw value (string)."""
    end = end if end is not None else len(payload)
    out: dict[str, str] = {}
    i = start
    while i < end:
        if i + 4 > end:
            break
        tag = payload[i : i + 2]
        length = int(payload[i + 2 : i + 4])
        value = payload[i + 4 : i + 4 + length]
        out[tag] = value
        i = i + 4 + length
    return out


def encode_tlvs(tlvs: list[TLV]) -> str:
    return "".join(t.encode() for t in tlvs)
