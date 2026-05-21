"""QR code rendering (PNG base64 + SVG) via segno."""

from __future__ import annotations

import base64
import io

import segno


def to_png_base64(payload: str, scale: int = 8) -> str:
    qr = segno.make(payload, error="M")
    buf = io.BytesIO()
    qr.save(buf, kind="png", scale=scale)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def to_svg(payload: str, scale: int = 8) -> str:
    qr = segno.make(payload, error="M")
    buf = io.BytesIO()
    qr.save(buf, kind="svg", scale=scale, xmldecl=False)
    return buf.getvalue().decode("utf-8")
