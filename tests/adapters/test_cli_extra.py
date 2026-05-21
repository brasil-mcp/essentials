"""Extra CLI subcommand smoke tests — drive each subcommand body to coverage.

Each CLI subcommand body (the lines inside `cli_*` handlers) emits a JSON
payload by calling the core function. We invoke each via `CliRunner` to make
sure the wiring works end-to-end and the JSON shape is what callers expect.
"""

from __future__ import annotations

import json

from typer.testing import CliRunner

from brasil_mcp.adapters.cli.app import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Validators (each one-liner body)
# ---------------------------------------------------------------------------


def test_validate_pis_subcommand() -> None:
    r = runner.invoke(app, ["validate-pis", "12056412348"])
    assert r.exit_code == 0, r.output
    payload = json.loads(r.stdout)
    assert "valid" in payload
    assert payload["raw"] == "12056412348"


def test_validate_renavam_subcommand() -> None:
    r = runner.invoke(app, ["validate-renavam", "00482397500"])
    assert r.exit_code == 0, r.output
    payload = json.loads(r.stdout)
    assert "valid" in payload
    assert payload["raw"] == "00482397500"


def test_validate_cnh_subcommand() -> None:
    r = runner.invoke(app, ["validate-cnh", "04607277401"])
    assert r.exit_code == 0, r.output
    payload = json.loads(r.stdout)
    assert "valid" in payload
    assert payload["raw"] == "04607277401"


def test_validate_titulo_eleitor_subcommand() -> None:
    # 12-digit título de eleitor (any input — we exercise the wrapper, not validity).
    r = runner.invoke(app, ["validate-titulo-eleitor", "123456789012"])
    assert r.exit_code == 0, r.output
    payload = json.loads(r.stdout)
    assert "valid" in payload
    assert payload["raw"] == "123456789012"


def test_validate_credit_card_subcommand() -> None:
    # 4111 1111 1111 1111 is Visa test card (Luhn-valid).
    r = runner.invoke(app, ["validate-credit-card", "4111111111111111"])
    assert r.exit_code == 0, r.output
    payload = json.loads(r.stdout)
    assert payload["valid"] is True
    assert payload["brand"] == "visa"


def test_validate_cnpj_subcommand_invalid_format_response() -> None:
    # Just exercises the subcommand body (already covered for valid above);
    # this one drives an invalid input through to make sure the wrapper still emits JSON.
    r = runner.invoke(app, ["validate-cnpj", "ABC"])
    assert r.exit_code == 0, r.output
    payload = json.loads(r.stdout)
    assert payload["valid"] is False


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------


def test_parse_pix_brcode_subcommand_invalid() -> None:
    r = runner.invoke(app, ["parse-pix-brcode", "not-a-brcode"])
    assert r.exit_code == 0, r.output
    payload = json.loads(r.stdout)
    assert payload["valid"] is False
    assert payload["error"]["code"] in {"INVALID_FORMAT", "UNSUPPORTED_FORMAT"}


def test_parse_pix_brcode_subcommand_roundtrip() -> None:
    # Generate a valid brcode then parse it back through the CLI.
    gen = runner.invoke(
        app,
        [
            "generate-pix-brcode",
            "--chave",
            "user@example.com",
            "--nome",
            "FULANO",
            "--cidade",
            "SAO PAULO",
        ],
    )
    assert gen.exit_code == 0
    brcode = json.loads(gen.stdout)["brcode"]
    parse = runner.invoke(app, ["parse-pix-brcode", brcode])
    assert parse.exit_code == 0, parse.output
    parsed = json.loads(parse.stdout)
    assert parsed["valid"] is True


# ---------------------------------------------------------------------------
# Calendar
# ---------------------------------------------------------------------------


def test_contar_dias_uteis_subcommand() -> None:
    r = runner.invoke(app, ["contar-dias-uteis", "2026-01-05", "2026-01-12"])
    assert r.exit_code == 0, r.output
    payload = json.loads(r.stdout)
    assert "count" in payload
    assert "total_dias" in payload
    assert "feriados_no_periodo" in payload


def test_listar_feriados_subcommand() -> None:
    r = runner.invoke(app, ["listar-feriados", "2026"])
    assert r.exit_code == 0, r.output
    payload = json.loads(r.stdout)
    assert payload["ano"] == 2026
    assert isinstance(payload["feriados"], list)
    assert len(payload["feriados"]) > 0


def test_proximo_dia_util_subcommand() -> None:
    r = runner.invoke(
        app, ["proximo-dia-util", "2026-09-06"]
    )  # domingo → 2026-09-08 (07 é feriado)
    assert r.exit_code == 0, r.output
    payload = json.loads(r.stdout)
    assert "date" in payload
    assert "dias_pulados" in payload


# ---------------------------------------------------------------------------
# Serve subcommand — wire `serve` body without actually running stdio loop.
# ---------------------------------------------------------------------------


def test_serve_subcommand_invokes_main(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Verifica que `serve` invoca brasil_mcp.adapters.mcp.server.main()."""
    called = {"ran": False}

    def fake_main() -> None:
        called["ran"] = True

    # Patch the module attribute that `cli_serve` imports lazily.
    import brasil_mcp.adapters.mcp.server as server_mod

    monkeypatch.setattr(server_mod, "main", fake_main)

    r = runner.invoke(app, ["serve"])
    assert r.exit_code == 0, r.output
    assert called["ran"] is True
