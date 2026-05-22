"""Tests for generate_whatsapp_qr."""

from __future__ import annotations

from brasil_mcp.core.whatsapp.qr import generate_whatsapp_qr


def test_success_no_message():
    r = generate_whatsapp_qr("11987654321")
    assert r["valid"] is True
    assert r["url"] == "https://wa.me/5511987654321"
    assert r["telefone_e164"] == "+5511987654321"
    assert r["qr_png_base64"] is None
    assert r["qr_svg"] is None


def test_success_with_message():
    r = generate_whatsapp_qr("11987654321", "Olá!")
    assert r["valid"] is True
    assert "wa.me/5511987654321?text=" in r["url"]
    # "Olá!" → "Ol%C3%A1%21"
    assert "Ol%C3%A1%21" in r["url"]


def test_qr_format_png():
    r = generate_whatsapp_qr("11987654321", qr_format="png")
    assert r["valid"] is True
    assert r["qr_png_base64"] is not None
    assert len(r["qr_png_base64"]) > 100
    assert r["qr_svg"] is None


def test_qr_format_svg():
    r = generate_whatsapp_qr("11987654321", qr_format="svg")
    assert r["qr_svg"] is not None
    assert r["qr_svg"].startswith("<svg") or r["qr_svg"].startswith("<?xml")


def test_qr_format_both():
    r = generate_whatsapp_qr("11987654321", qr_format="both")
    assert r["qr_png_base64"] is not None
    assert r["qr_svg"] is not None


def test_invalid_qr_format():
    r = generate_whatsapp_qr("11987654321", qr_format="bogus")
    assert r["valid"] is False
    assert r["error"]["code"] == "INVALID_FORMAT"


def test_invalid_telefone_propagates_error():
    r = generate_whatsapp_qr("123")
    assert r["valid"] is False
    assert r["error"]["code"] == "INVALID_LENGTH"


def test_empty_telefone():
    r = generate_whatsapp_qr("")
    assert r["valid"] is False


def test_empty_message_treated_as_none():
    r1 = generate_whatsapp_qr("11987654321", mensagem="")
    r2 = generate_whatsapp_qr("11987654321", mensagem="   ")
    r3 = generate_whatsapp_qr("11987654321")
    assert r1["url"] == r2["url"] == r3["url"]


def test_message_truncated_at_1024():
    long_msg = "A" * 2000
    r = generate_whatsapp_qr("11987654321", mensagem=long_msg)
    assert r["valid"] is True
    # URL contains exactly 1024 'A' chars (URL-encoded, but A is safe so no encoding)
    assert r["url"].count("A") == 1024


def test_message_with_special_chars_url_encoded():
    r = generate_whatsapp_qr("11987654321", mensagem="hello & goodbye")
    # & should be %26 in the URL
    assert "%26" in r["url"]
