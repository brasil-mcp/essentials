"""PIX BR Code parser + generator (EMV TLV format)."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from brasil_mcp.core.errors import ErrorCode, ErrorObj
from brasil_mcp.core.models import ValidationResult
from brasil_mcp.core.pix.brcode import TLV, decode_tlv, encode_tlvs
from brasil_mcp.core.pix.crc16 import crc16_hex
from brasil_mcp.core.pix.qr import to_png_base64, to_svg

# Top-level EMV tag IDs (per BCB PIX spec).
_TAG_PAYLOAD_FORMAT = "00"
_TAG_MERCHANT_ACCOUNT = "26"
_TAG_MERCHANT_CATEGORY = "52"
_TAG_CURRENCY = "53"
_TAG_AMOUNT = "54"
_TAG_COUNTRY = "58"
_TAG_MERCHANT_NAME = "59"
_TAG_MERCHANT_CITY = "60"
_TAG_ADDITIONAL_DATA = "62"
_TAG_CRC = "63"

# Sub-TLVs inside merchant-account (tag 26).
_MA_GUI = "00"
_MA_CHAVE = "01"
_MA_DESC = "02"
_MA_URL = "25"

# Sub-TLVs inside additional-data (tag 62).
_AD_TXID = "05"

_PIX_GUI = "BR.GOV.BCB.PIX"
_CURRENCY_BRL = "986"
_COUNTRY_BR = "BR"
_DEFAULT_MCC = "0000"
_PAYLOAD_FORMAT_VALUE = "01"

# Field length limits per BCB spec.
_MAX_NAME = 25
_MAX_CITY = 15
_MAX_TXID = 25
_MAX_DESC = 72

_VALID_QR_FORMATS = {"none", "png", "svg", "both"}

_UUID_V4_RE = re.compile(
    r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$",
    re.IGNORECASE,
)
_DIGITS_ONLY_RE = re.compile(r"^\d+$")


def _strip_accents_upper(s: str) -> str:
    nfkd = unicodedata.normalize("NFKD", s)
    no_combining = "".join(ch for ch in nfkd if not unicodedata.combining(ch))
    return no_combining.upper()


def _classify_chave(chave: str) -> str:
    if not chave:
        return "aleatoria"
    if "@" in chave:
        return "email"
    if chave.startswith("+"):
        digits = re.sub(r"\D", "", chave)
        if len(digits) >= 12:
            return "telefone"
    if _DIGITS_ONLY_RE.match(chave):
        if len(chave) == 11:
            return "cpf"
        if len(chave) == 14:
            return "cnpj"
    if _UUID_V4_RE.match(chave):
        return "aleatoria"
    return "aleatoria"


def _truncate(value: str, max_len: int) -> str:
    return value if len(value) <= max_len else value[:max_len]


def parse_pix_brcode(value: str) -> ValidationResult:
    """Decode a PIX BR Code string. Returns ValidationResult with extras populated."""
    raw = value or ""
    payload = raw.strip()

    if not payload:
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.EMPTY_INPUT,
                "BR Code não pode ser vazio.",
                "BR Code cannot be empty.",
            ),
        )

    # Minimum sanity: must contain the CRC tail (6304XXXX).
    if len(payload) < 8 or payload[-8:-4] != "6304":
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.INVALID_FORMAT,
                "BR Code não termina com tag CRC (6304).",
                "BR Code does not end with CRC tag (6304).",
                suggestion="Verifique se o payload está completo.",
            ),
        )

    body = payload[:-4]  # everything before the 4-char CRC value
    crc_received = payload[-4:].upper()
    crc_expected = crc16_hex(body)
    if crc_received != crc_expected:
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.INVALID_CHECKSUM,
                f"CRC inválido: esperado {crc_expected}, recebido {crc_received}.",
                f"Invalid CRC: expected {crc_expected}, got {crc_received}.",
            ),
        )

    # Top-level TLV decode.
    try:
        top = decode_tlv(payload)
    except (ValueError, IndexError):
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.INVALID_FORMAT,
                "BR Code malformado (TLV inválido).",
                "Malformed BR Code (invalid TLV).",
            ),
        )

    # Verify payload format indicator.
    if top.get(_TAG_PAYLOAD_FORMAT) != _PAYLOAD_FORMAT_VALUE:
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.UNSUPPORTED_FORMAT,
                "Payload format indicator ausente ou não suportado.",
                "Payload format indicator missing or unsupported.",
            ),
        )

    merchant_account_raw = top.get(_TAG_MERCHANT_ACCOUNT)
    if not merchant_account_raw:
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.UNSUPPORTED_FORMAT,
                "Tag 26 (merchant account info) ausente — não é um BR Code PIX.",
                "Tag 26 (merchant account info) missing — not a PIX BR Code.",
            ),
        )

    try:
        ma_subs = decode_tlv(merchant_account_raw)
    except (ValueError, IndexError):
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.INVALID_FORMAT,
                "Sub-TLVs da tag 26 inválidos.",
                "Tag 26 sub-TLVs invalid.",
            ),
        )

    gui = ma_subs.get(_MA_GUI, "")
    if gui != _PIX_GUI:
        return ValidationResult(
            valid=False,
            raw=raw,
            error=ErrorObj(
                ErrorCode.UNSUPPORTED_FORMAT,
                f"GUI '{gui}' não é PIX (esperado '{_PIX_GUI}').",
                f"GUI '{gui}' is not PIX (expected '{_PIX_GUI}').",
            ),
        )

    chave = ma_subs.get(_MA_CHAVE, "") or ""
    descricao = ma_subs.get(_MA_DESC) or None
    url_provedor = ma_subs.get(_MA_URL) or None
    dinamico = url_provedor is not None

    beneficiario = top.get(_TAG_MERCHANT_NAME, "")
    cidade = top.get(_TAG_MERCHANT_CITY, "")

    # Amount parsing (decimal → cents int).
    amount_str = top.get(_TAG_AMOUNT)
    valor: int | None = None
    if amount_str:
        try:
            valor = round(float(amount_str) * 100)
        except ValueError:
            return ValidationResult(
                valid=False,
                raw=raw,
                error=ErrorObj(
                    ErrorCode.INVALID_FORMAT,
                    f"Valor inválido na tag 54: '{amount_str}'.",
                    f"Invalid amount in tag 54: '{amount_str}'.",
                ),
            )

    moeda_code = top.get(_TAG_CURRENCY, _CURRENCY_BRL)
    moeda = "BRL" if moeda_code == _CURRENCY_BRL else moeda_code

    # txid lives in sub-TLV 05 of tag 62.
    txid: str | None = None
    additional_data_raw = top.get(_TAG_ADDITIONAL_DATA)
    if additional_data_raw:
        try:
            ad_subs = decode_tlv(additional_data_raw)
        except (ValueError, IndexError):
            ad_subs = {}
        txid_val = ad_subs.get(_AD_TXID)
        if txid_val and txid_val != "***":
            txid = txid_val

    extras: dict[str, Any] = {
        "chave": chave,
        "tipo_chave": _classify_chave(chave),
        "beneficiario": beneficiario,
        "cidade": cidade,
        "valor": valor,
        "moeda": moeda,
        "txid": txid,
        "descricao": descricao,
        "dinamico": dinamico,
        "url_provedor": url_provedor,
    }

    return ValidationResult(valid=True, raw=raw, formatted=payload, extras=extras)


def _error_dict(code: ErrorCode, pt: str, en: str, suggestion: str | None = None) -> dict[str, Any]:
    return ErrorObj(code, pt, en, suggestion).to_dict()


def generate_pix_brcode(
    chave: str,
    nome_beneficiario: str,
    cidade: str,
    valor: int | None = None,
    txid: str | None = None,
    descricao: str | None = None,
    qr_format: str = "none",
) -> dict[str, Any]:
    """Generate a static PIX BR Code from inputs. Returns a dict."""
    result: dict[str, Any] = {
        "brcode": None,
        "qr_png_base64": None,
        "qr_svg": None,
        "error": None,
    }

    if not chave or not chave.strip():
        result["error"] = _error_dict(
            ErrorCode.MISSING_REQUIRED_FIELD,
            "Chave PIX é obrigatória.",
            "PIX key is required.",
        )
        return result

    if qr_format not in _VALID_QR_FORMATS:
        result["error"] = _error_dict(
            ErrorCode.INVALID_FORMAT,
            f"qr_format inválido: '{qr_format}'. Use one of: {sorted(_VALID_QR_FORMATS)}.",
            f"Invalid qr_format: '{qr_format}'. Use one of: {sorted(_VALID_QR_FORMATS)}.",
        )
        return result

    chave_clean = chave.strip()
    nome_clean = _truncate(_strip_accents_upper((nome_beneficiario or "").strip()), _MAX_NAME)
    cidade_clean = _truncate(_strip_accents_upper((cidade or "").strip()), _MAX_CITY)
    desc_clean = _truncate(descricao.strip(), _MAX_DESC) if descricao else None
    txid_clean = _truncate(txid.strip(), _MAX_TXID) if txid else None

    # Build merchant-account sub-TLVs (tag 26).
    ma_tlvs: list[TLV] = [TLV(_MA_GUI, _PIX_GUI), TLV(_MA_CHAVE, chave_clean)]
    if desc_clean:
        ma_tlvs.append(TLV(_MA_DESC, desc_clean))
    merchant_account_value = encode_tlvs(ma_tlvs)

    # Build additional-data sub-TLVs (tag 62) — txid (or "***" placeholder).
    ad_value = encode_tlvs([TLV(_AD_TXID, txid_clean if txid_clean else "***")])

    # Assemble top-level TLVs.
    top_tlvs: list[TLV] = [
        TLV(_TAG_PAYLOAD_FORMAT, _PAYLOAD_FORMAT_VALUE),
        TLV(_TAG_MERCHANT_ACCOUNT, merchant_account_value),
        TLV(_TAG_MERCHANT_CATEGORY, _DEFAULT_MCC),
        TLV(_TAG_CURRENCY, _CURRENCY_BRL),
    ]

    if valor is not None and valor > 0:
        amount_str = f"{valor / 100:.2f}"
        top_tlvs.append(TLV(_TAG_AMOUNT, amount_str))

    top_tlvs.extend(
        [
            TLV(_TAG_COUNTRY, _COUNTRY_BR),
            TLV(_TAG_MERCHANT_NAME, nome_clean),
            TLV(_TAG_MERCHANT_CITY, cidade_clean),
            TLV(_TAG_ADDITIONAL_DATA, ad_value),
        ]
    )

    body = encode_tlvs(top_tlvs)
    # CRC field: tag "63", length "04", then the 4 hex chars.
    crc_input = body + "6304"
    crc = crc16_hex(crc_input)
    brcode = crc_input + crc

    result["brcode"] = brcode

    if qr_format in ("png", "both"):
        result["qr_png_base64"] = to_png_base64(brcode)
    if qr_format in ("svg", "both"):
        result["qr_svg"] = to_svg(brcode)

    return result
