"""Registra cada core function como uma MCP tool com schema apropriado."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from brasil_mcp.core.boleto.parser import parse_boleto as core_parse_boleto
from brasil_mcp.core.calendar.feriados import (
    contar_dias_uteis as core_contar_dias_uteis,
)
from brasil_mcp.core.calendar.feriados import (
    is_feriado_nacional as core_is_feriado,
)
from brasil_mcp.core.calendar.feriados import (
    listar_feriados as core_listar_feriados,
)
from brasil_mcp.core.calendar.feriados import (
    proximo_dia_util as core_proximo_dia_util,
)
from brasil_mcp.core.pix.parser import (
    generate_pix_brcode as core_generate_pix,
)
from brasil_mcp.core.pix.parser import (
    parse_pix_brcode as core_parse_pix,
)
from brasil_mcp.core.telemetry import track
from brasil_mcp.core.validators.cnh import validate_cnh as core_validate_cnh
from brasil_mcp.core.validators.cnpj import validate_cnpj as core_validate_cnpj
from brasil_mcp.core.validators.cpf import validate_cpf as core_validate_cpf
from brasil_mcp.core.validators.credit_card import (
    validate_credit_card as core_validate_credit_card,
)
from brasil_mcp.core.validators.pis import validate_pis as core_validate_pis
from brasil_mcp.core.validators.renavam import validate_renavam as core_validate_renavam
from brasil_mcp.core.validators.titulo_eleitor import (
    validate_titulo_eleitor as core_validate_titulo,
)


def register_tools(mcp: FastMCP) -> None:
    """Registra todas as 14 tools no servidor FastMCP."""

    @mcp.tool()
    def validate_cpf(value: str) -> dict[str, Any]:
        """Valida CPF brasileiro (11 dígitos). Módulo 11. Rejeita sequências repetidas."""
        with track("validate_cpf"):
            return core_validate_cpf(value).to_dict()

    @mcp.tool()
    def validate_cnpj(value: str) -> dict[str, Any]:
        """Valida CNPJ brasileiro — legacy (14 dígitos) E novo alfanumérico (Receita Federal NT COCAD/SUARA 49/2024). Auto-detecta."""
        with track("validate_cnpj"):
            return core_validate_cnpj(value).to_dict()

    @mcp.tool()
    def validate_pis(value: str) -> dict[str, Any]:
        """Valida PIS/PASEP/NIT (11 dígitos)."""
        with track("validate_pis"):
            return core_validate_pis(value).to_dict()

    @mcp.tool()
    def validate_renavam(value: str) -> dict[str, Any]:
        """Valida RENAVAM (11 dígitos)."""
        with track("validate_renavam"):
            return core_validate_renavam(value).to_dict()

    @mcp.tool()
    def validate_cnh(value: str) -> dict[str, Any]:
        """Valida CNH brasileira (11 dígitos)."""
        with track("validate_cnh"):
            return core_validate_cnh(value).to_dict()

    @mcp.tool()
    def validate_titulo_eleitor(value: str) -> dict[str, Any]:
        """Valida título de eleitor (12 dígitos)."""
        with track("validate_titulo_eleitor"):
            return core_validate_titulo(value).to_dict()

    @mcp.tool()
    def validate_credit_card(value: str) -> dict[str, Any]:
        """Valida cartão de crédito (Luhn) e detecta bandeira: Visa, Mastercard, Elo, Hipercard, Amex, Diners, JCB, Discover."""
        with track("validate_credit_card"):
            return core_validate_credit_card(value).to_dict()

    @mcp.tool()
    def parse_boleto(value: str) -> dict[str, Any]:
        """Parse boleto bancário (47 linha digitável / 44 código de barras) OU arrecadação (48). Detecta tipo automaticamente."""
        with track("parse_boleto"):
            return core_parse_boleto(value).to_dict()

    @mcp.tool()
    def parse_pix_brcode(value: str) -> dict[str, Any]:
        """Parse BR Code PIX (string EMV). Retorna chave, beneficiário, valor, txid, descrição."""
        with track("parse_pix_brcode"):
            return core_parse_pix(value).to_dict()

    @mcp.tool()
    def generate_pix_brcode(
        chave: str,
        nome_beneficiario: str,
        cidade: str,
        valor: int | None = None,
        txid: str | None = None,
        descricao: str | None = None,
        qr_format: str = "none",
    ) -> dict[str, Any]:
        """Gera BR Code PIX estático. qr_format: 'none' | 'png' | 'svg' | 'both'."""
        with track("generate_pix_brcode"):
            return core_generate_pix(
                chave, nome_beneficiario, cidade, valor, txid, descricao, qr_format
            )

    @mcp.tool()
    def is_feriado_nacional(
        date: str, uf: str | None = None, municipio: str | None = None
    ) -> dict[str, Any]:
        """Verifica se uma data (YYYY-MM-DD) é feriado brasileiro. UF opcional para estaduais."""
        with track("is_feriado_nacional"):
            return core_is_feriado(date, uf=uf, municipio=municipio)

    @mcp.tool()
    def proximo_dia_util(
        date: str, uf: str | None = None, include_today: bool = False
    ) -> dict[str, Any]:
        """Retorna o próximo dia útil após uma data. Pula fins de semana e feriados."""
        with track("proximo_dia_util"):
            return core_proximo_dia_util(date, uf=uf, include_today=include_today)

    @mcp.tool()
    def contar_dias_uteis(
        start_date: str,
        end_date: str,
        uf: str | None = None,
        inclusive_end: bool = False,
    ) -> dict[str, Any]:
        """Conta dias úteis entre duas datas (inclui início, exclui fim por padrão)."""
        with track("contar_dias_uteis"):
            return core_contar_dias_uteis(start_date, end_date, uf=uf, inclusive_end=inclusive_end)

    @mcp.tool()
    def listar_feriados(year: int, uf: str | None = None) -> dict[str, Any]:
        """Lista feriados brasileiros num ano. UF opcional para incluir estaduais."""
        with track("listar_feriados"):
            return core_listar_feriados(year, uf=uf)
