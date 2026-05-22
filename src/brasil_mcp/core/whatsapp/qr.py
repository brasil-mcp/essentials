"""generate_whatsapp_qr — link wa.me + QR opcional.

WhatsApp tem deeplink universal `https://wa.me/<E164-sem-+>?text=<msg url-encoded>`
que abre conversa direto com o número informado, em qualquer plataforma.
Útil pra cartões de visita, signature de email, atendimento ao cliente.

Reusa:
- `validate_telefone` pra normalizar/validar o número.
- `core.pix.qr.to_png_base64` / `to_svg` pra renderizar o QR.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from brasil_mcp.core.errors import ErrorCode, ErrorObj
from brasil_mcp.core.pix.qr import to_png_base64, to_svg
from brasil_mcp.core.validators.telefone import validate_telefone

WA_ME_URL = "https://wa.me/{numero}"
WA_ME_URL_COM_MSG = "https://wa.me/{numero}?text={msg}"

_VALID_QR_FORMATS = {"none", "png", "svg", "both"}
_MAX_MSG = 1024


def generate_whatsapp_qr(
    telefone: str,
    mensagem: str | None = None,
    qr_format: str = "none",
) -> dict[str, Any]:
    """Gera link wa.me + QR opcional pra um número de telefone brasileiro.

    Args:
        telefone: telefone BR (qualquer máscara, com ou sem +55).
        mensagem: opcional, mensagem pré-preenchida ao abrir a conversa.
                  Max 1024 chars (truncada se exceder).
        qr_format: 'none' | 'png' | 'svg' | 'both'.

    Returns: { valid, url, telefone_e164, qr_png_base64, qr_svg, error }.
    """
    result: dict[str, Any] = {
        "valid": False,
        "url": None,
        "telefone_e164": None,
        "qr_png_base64": None,
        "qr_svg": None,
        "error": None,
    }

    if qr_format not in _VALID_QR_FORMATS:
        result["error"] = ErrorObj(
            ErrorCode.INVALID_FORMAT,
            f"qr_format inválido: '{qr_format}'. Use one of: {sorted(_VALID_QR_FORMATS)}.",
            f"Invalid qr_format: '{qr_format}'. Use one of: {sorted(_VALID_QR_FORMATS)}.",
        ).to_dict()
        return result

    tel_result = validate_telefone(telefone)
    if not tel_result.valid:
        # Bubble up the telefone error directly — caller doesn't need to
        # know the difference between "bad number" types.
        result["error"] = (
            tel_result.error.to_dict()
            if tel_result.error
            else ErrorObj(
                ErrorCode.INVALID_FORMAT,
                "Telefone inválido.",
                "Invalid telefone.",
            ).to_dict()
        )
        return result

    # E.164 sem o "+" pra montar wa.me (formato exigido pelo WhatsApp)
    e164 = tel_result.extras["e164"]
    numero_sem_plus = e164[1:]  # strip "+"

    msg_clean: str | None = None
    if mensagem:
        msg_stripped = mensagem.strip()
        if msg_stripped:
            msg_clean = msg_stripped[:_MAX_MSG]

    if msg_clean:
        url = WA_ME_URL_COM_MSG.format(numero=numero_sem_plus, msg=quote(msg_clean, safe=""))
    else:
        url = WA_ME_URL.format(numero=numero_sem_plus)

    result["valid"] = True
    result["url"] = url
    result["telefone_e164"] = e164
    if qr_format in ("png", "both"):
        result["qr_png_base64"] = to_png_base64(url)
    if qr_format in ("svg", "both"):
        result["qr_svg"] = to_svg(url)
    return result
