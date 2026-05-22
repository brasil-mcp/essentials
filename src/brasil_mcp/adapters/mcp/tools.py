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
from brasil_mcp.core.lookups.banco import lookup_banco_febraban as core_lookup_banco
from brasil_mcp.core.lookups.cep import lookup_cep as core_lookup_cep
from brasil_mcp.core.lookups.cep import lookup_endereco_cep as core_lookup_endereco_cep
from brasil_mcp.core.lookups.cotacao import lookup_cotacao_brl as core_lookup_cotacao
from brasil_mcp.core.lookups.ddd import lookup_ddd as core_lookup_ddd
from brasil_mcp.core.lookups.ibge import lookup_ibge_municipio as core_lookup_ibge
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
from brasil_mcp.core.validators.telefone import validate_telefone as core_validate_telefone
from brasil_mcp.core.validators.titulo_eleitor import (
    validate_titulo_eleitor as core_validate_titulo,
)
from brasil_mcp.core.whatsapp.qr import generate_whatsapp_qr as core_generate_whatsapp_qr


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

    @mcp.tool()
    def lookup_cep(cep: str) -> dict[str, Any]:
        """Consulta endereço de CEP brasileiro via ViaCEP (online). Retorna logradouro, bairro, cidade, UF, IBGE code, DDD. Resultado cacheado localmente por 30 dias."""
        with track("lookup_cep"):
            return core_lookup_cep(cep)

    @mcp.tool()
    def lookup_banco_febraban(codigo: str) -> dict[str, Any]:
        """Consulta banco brasileiro por código FEBRABAN (3 dígitos) via BrasilAPI (online). Cobre 200+ bancos. Cacheado 7 dias."""
        with track("lookup_banco_febraban"):
            return core_lookup_banco(codigo)

    @mcp.tool()
    def lookup_ddd(ddd: str) -> dict[str, Any]:
        """Consulta UF e lista de municípios por código DDD (2 dígitos) via BrasilAPI (online). Cacheado 90 dias."""
        with track("lookup_ddd"):
            return core_lookup_ddd(ddd)

    @mcp.tool()
    def lookup_ibge_municipio(nome: str, uf: str | None = None) -> dict[str, Any]:
        """Consulta código IBGE de município brasileiro por nome (acento-insensível). UF opcional. Cacheado 30 dias."""
        with track("lookup_ibge_municipio"):
            return core_lookup_ibge(nome, uf=uf)

    @mcp.tool()
    def lookup_cotacao_brl(moeda: str, data_cotacao: str | None = None) -> dict[str, Any]:
        """Consulta cotação PTAX BRL via Banco Central. Moedas: USD, EUR, GBP, JPY, ARS, CHF, CAD, AUD. data_cotacao opcional (default hoje). Cacheado 1h pra recente, 1 ano pra histórico."""
        with track("lookup_cotacao_brl"):
            return core_lookup_cotacao(moeda, data_cotacao=data_cotacao)

    @mcp.tool()
    def lookup_endereco_cep(uf: str, cidade: str, logradouro: str) -> dict[str, Any]:
        """Busca lista de CEPs por endereço (UF + cidade + logradouro) via ViaCEP (online). Aceita match parcial no logradouro. Cacheado 30 dias."""
        with track("lookup_endereco_cep"):
            return core_lookup_endereco_cep(uf, cidade, logradouro)

    @mcp.tool()
    def validate_telefone(value: str) -> dict[str, Any]:
        """Valida e formata telefone brasileiro (celular 11 dígitos ou fixo 10). Aceita com/sem +55, qualquer máscara. Retorna formatted, formatted_international, e164, ddd, tipo (celular/fixo)."""
        with track("validate_telefone"):
            return core_validate_telefone(value).to_dict()

    @mcp.tool()
    def generate_whatsapp_qr(
        telefone: str, mensagem: str | None = None, qr_format: str = "none"
    ) -> dict[str, Any]:
        """Gera link wa.me (deeplink WhatsApp) + QR opcional pra telefone brasileiro. mensagem opcional (URL-encoded). qr_format: 'none' | 'png' | 'svg' | 'both'."""
        with track("generate_whatsapp_qr"):
            return core_generate_whatsapp_qr(telefone, mensagem, qr_format)
