"""Tests para o adapter CLI Typer."""

from __future__ import annotations

import json

from typer.testing import CliRunner

import brasil_mcp
from brasil_mcp.adapters.cli.app import app

runner = CliRunner()


def test_version() -> None:
    r = runner.invoke(app, ["version"])
    assert r.exit_code == 0, r.output
    assert r.stdout.strip() == brasil_mcp.__version__


def test_validate_cpf_valid() -> None:
    r = runner.invoke(app, ["validate-cpf", "52998224725"])
    assert r.exit_code == 0, r.output
    payload = json.loads(r.stdout)
    assert payload["valid"] is True
    assert payload["raw"] == "52998224725"


def test_validate_cpf_invalid() -> None:
    r = runner.invoke(app, ["validate-cpf", "12345678900"])
    assert r.exit_code == 0, r.output
    payload = json.loads(r.stdout)
    assert payload["valid"] is False


def test_validate_cnpj_legacy() -> None:
    r = runner.invoke(app, ["validate-cnpj", "11222333000181"])
    assert r.exit_code == 0, r.output
    payload = json.loads(r.stdout)
    assert payload["valid"] is True
    assert payload["format"] == "legacy"


def test_generate_pix_brcode() -> None:
    r = runner.invoke(
        app,
        [
            "generate-pix-brcode",
            "--chave",
            "email@example.com",
            "--nome",
            "Fulano",
            "--cidade",
            "SAO PAULO",
        ],
    )
    assert r.exit_code == 0, r.output
    payload = json.loads(r.stdout)
    assert payload["brcode"]
    assert payload["error"] is None


def test_is_feriado_independencia() -> None:
    r = runner.invoke(app, ["is-feriado", "2026-09-07"])
    assert r.exit_code == 0, r.output
    payload = json.loads(r.stdout)
    assert payload["is_feriado"] is True


def test_parse_boleto_empty() -> None:
    r = runner.invoke(app, ["parse-boleto", ""])
    assert r.exit_code == 0, r.output
    payload = json.loads(r.stdout)
    assert payload["valid"] is False
    assert payload["error"]["code"] == "EMPTY_INPUT"


def test_help_lists_subcommands() -> None:
    r = runner.invoke(app, ["--help"])
    assert r.exit_code == 0
    # spot-check: deve listar subcomandos principais
    for cmd in ("validate-cpf", "parse-boleto", "generate-pix-brcode", "serve", "version"):
        assert cmd in r.stdout
