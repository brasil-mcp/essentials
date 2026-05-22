"""CLI Typer: brasil-mcp <subcommand>. Subcomando 'serve' inicia stdio MCP."""

from __future__ import annotations

import json
from typing import Any

import typer

from brasil_mcp.core.boleto.parser import parse_boleto as core_parse_boleto
from brasil_mcp.core.calendar.feriados import (
    contar_dias_uteis as core_contar,
)
from brasil_mcp.core.calendar.feriados import (
    is_feriado_nacional as core_is_feriado,
)
from brasil_mcp.core.calendar.feriados import (
    listar_feriados as core_listar,
)
from brasil_mcp.core.calendar.feriados import (
    proximo_dia_util as core_prox,
)
from brasil_mcp.core.pix.parser import (
    generate_pix_brcode as core_gen_pix,
)
from brasil_mcp.core.pix.parser import (
    parse_pix_brcode as core_parse_pix,
)
from brasil_mcp.core.validators.cnh import validate_cnh as core_cnh
from brasil_mcp.core.validators.cnpj import validate_cnpj as core_cnpj
from brasil_mcp.core.validators.cpf import validate_cpf as core_cpf
from brasil_mcp.core.validators.credit_card import validate_credit_card as core_cc
from brasil_mcp.core.validators.pis import validate_pis as core_pis
from brasil_mcp.core.validators.renavam import validate_renavam as core_renavam
from brasil_mcp.core.validators.titulo_eleitor import (
    validate_titulo_eleitor as core_titulo,
)

app = typer.Typer(
    name="brasil-mcp",
    help="MCP server brasileiro + CLI. Validators, boleto, PIX, calendário.",
    no_args_is_help=True,
)


def _emit(data: Any) -> None:
    """Imprime data como JSON, preservando caracteres unicode (acentos PT)."""
    typer.echo(json.dumps(data, ensure_ascii=False, indent=2))


@app.command("validate-cpf")
def cli_validate_cpf(value: str) -> None:
    """Valida CPF (11 dígitos)."""
    _emit(core_cpf(value).to_dict())


@app.command("validate-cnpj")
def cli_validate_cnpj(value: str) -> None:
    """Valida CNPJ (legacy 14 dígitos OU alfanumérico novo)."""
    _emit(core_cnpj(value).to_dict())


@app.command("validate-pis")
def cli_validate_pis(value: str) -> None:
    """Valida PIS/PASEP/NIT (11 dígitos)."""
    _emit(core_pis(value).to_dict())


@app.command("validate-renavam")
def cli_validate_renavam(value: str) -> None:
    """Valida RENAVAM (11 dígitos)."""
    _emit(core_renavam(value).to_dict())


@app.command("validate-cnh")
def cli_validate_cnh(value: str) -> None:
    """Valida CNH (11 dígitos)."""
    _emit(core_cnh(value).to_dict())


@app.command("validate-titulo-eleitor")
def cli_validate_titulo(value: str) -> None:
    """Valida título de eleitor (12 dígitos)."""
    _emit(core_titulo(value).to_dict())


@app.command("validate-credit-card")
def cli_validate_cc(value: str) -> None:
    """Valida cartão de crédito (Luhn) e detecta bandeira."""
    _emit(core_cc(value).to_dict())


@app.command("parse-boleto")
def cli_parse_boleto(value: str) -> None:
    """Parse boleto bancário ou arrecadação."""
    _emit(core_parse_boleto(value).to_dict())


@app.command("parse-pix-brcode")
def cli_parse_pix(value: str) -> None:
    """Parse BR Code PIX (string EMV)."""
    _emit(core_parse_pix(value).to_dict())


@app.command("generate-pix-brcode")
def cli_gen_pix(
    chave: str = typer.Option(..., help="Chave PIX"),
    nome: str = typer.Option(..., help="Nome do beneficiário (max 25 chars ASCII)"),
    cidade: str = typer.Option(..., help="Cidade (max 15 chars ASCII)"),
    valor: int | None = typer.Option(None, help="Valor em centavos"),
    txid: str | None = typer.Option(None, help="Identificador de transação"),
    descricao: str | None = typer.Option(None, help="Descrição"),
    qr: str = typer.Option("none", help="Formato do QR: none|png|svg|both"),
) -> None:
    """Gera BR Code PIX estático."""
    _emit(core_gen_pix(chave, nome, cidade, valor, txid, descricao, qr))


@app.command("is-feriado")
def cli_is_feriado(
    date: str,
    uf: str | None = typer.Option(None, help="UF para feriados estaduais"),
) -> None:
    """Verifica se uma data (YYYY-MM-DD) é feriado brasileiro."""
    _emit(core_is_feriado(date, uf=uf))


@app.command("proximo-dia-util")
def cli_prox(
    date: str,
    uf: str | None = typer.Option(None, help="UF para feriados estaduais"),
    include_today: bool = typer.Option(False, help="Considerar a data atual no resultado"),
) -> None:
    """Retorna o próximo dia útil após uma data."""
    _emit(core_prox(date, uf=uf, include_today=include_today))


@app.command("contar-dias-uteis")
def cli_contar(
    start_date: str,
    end_date: str,
    uf: str | None = typer.Option(None, help="UF para feriados estaduais"),
    inclusive_end: bool = typer.Option(False, help="Incluir a data final na contagem"),
) -> None:
    """Conta dias úteis entre duas datas."""
    _emit(core_contar(start_date, end_date, uf=uf, inclusive_end=inclusive_end))


@app.command("listar-feriados")
def cli_listar(
    year: int,
    uf: str | None = typer.Option(None, help="UF para incluir feriados estaduais"),
) -> None:
    """Lista feriados brasileiros num ano."""
    _emit(core_listar(year, uf=uf))


@app.command("serve")
def cli_serve() -> None:
    """Inicia o servidor MCP via stdio."""
    from brasil_mcp.adapters.mcp.server import main as run_mcp_server

    run_mcp_server()


@app.command("version")
def cli_version() -> None:
    """Exibe a versão do pacote."""
    import brasil_mcp

    typer.echo(brasil_mcp.__version__)


# ----- Lookups online (v0.2) -----


@app.command("lookup-cep")
def cli_lookup_cep(cep: str) -> None:
    """Consulta endereço por CEP via ViaCEP (online)."""
    from brasil_mcp.core.lookups.cep import lookup_cep

    _emit(lookup_cep(cep))


@app.command("lookup-banco-febraban")
def cli_lookup_banco(codigo: str) -> None:
    """Consulta banco brasileiro por código FEBRABAN via BrasilAPI (online)."""
    from brasil_mcp.core.lookups.banco import lookup_banco_febraban

    _emit(lookup_banco_febraban(codigo))


@app.command("lookup-ddd")
def cli_lookup_ddd(ddd: str) -> None:
    """Consulta UF e municípios por código DDD via BrasilAPI (online)."""
    from brasil_mcp.core.lookups.ddd import lookup_ddd

    _emit(lookup_ddd(ddd))


@app.command("lookup-ibge-municipio")
def cli_lookup_ibge(
    nome: str,
    uf: str | None = typer.Option(None, help="UF pra restringir a busca"),
) -> None:
    """Consulta código IBGE de município por nome (online)."""
    from brasil_mcp.core.lookups.ibge import lookup_ibge_municipio

    _emit(lookup_ibge_municipio(nome, uf=uf))


@app.command("lookup-cotacao-brl")
def cli_lookup_cotacao(
    moeda: str,
    data: str | None = typer.Option(None, help="Data ISO YYYY-MM-DD; default hoje"),
) -> None:
    """Consulta cotação PTAX BRL no Banco Central (online). USD, EUR, GBP, JPY, ARS, CHF, CAD, AUD."""
    from brasil_mcp.core.lookups.cotacao import lookup_cotacao_brl

    _emit(lookup_cotacao_brl(moeda, data_cotacao=data))
