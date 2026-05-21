"""Testes para o módulo de telemetria opt-in."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from brasil_mcp.core import telemetry


@pytest.fixture(autouse=True)
def _isolate_filesystem(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Isola o filesystem para cada teste — nunca toca em ~/.local/share/brasil-mcp."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    # Reset client cache between tests.
    monkeypatch.setattr(telemetry, "_posthog_client", None)


# ---------------------------------------------------------------------------
# _is_enabled
# ---------------------------------------------------------------------------


class TestIsEnabled:
    def test_false_por_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("BRASIL_MCP_TELEMETRY", raising=False)
        assert telemetry._is_enabled() is False

    @pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "YES", "on", "ON", "True"])
    def test_true_para_valores_truthy(
        self, monkeypatch: pytest.MonkeyPatch, value: str
    ) -> None:
        monkeypatch.setenv("BRASIL_MCP_TELEMETRY", value)
        assert telemetry._is_enabled() is True

    @pytest.mark.parametrize("value", ["0", "false", "no", "off", "", "anything"])
    def test_false_para_valores_falsy(
        self, monkeypatch: pytest.MonkeyPatch, value: str
    ) -> None:
        monkeypatch.setenv("BRASIL_MCP_TELEMETRY", value)
        assert telemetry._is_enabled() is False


# ---------------------------------------------------------------------------
# track_tool_call (no-op quando desabilitado)
# ---------------------------------------------------------------------------


class TestTrackToolCallNoOp:
    def test_no_op_quando_desabilitado(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("BRASIL_MCP_TELEMETRY", raising=False)
        # Não deve lançar nem realizar I/O (posthog não é importado).
        telemetry.track_tool_call("validate_cpf", success=True, latency_ms=1.2)

    def test_no_op_mesmo_sem_posthog(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Mesmo se opt-in, se posthog não estiver disponível, vira no-op silencioso.
        monkeypatch.setenv("BRASIL_MCP_TELEMETRY", "1")

        import builtins

        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):  # type: ignore[no-untyped-def]
            if name == "posthog":
                raise ImportError("posthog não instalado")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        # Não deve lançar.
        telemetry.track_tool_call("validate_cpf", success=True, latency_ms=1.2)


# ---------------------------------------------------------------------------
# maybe_show_notice
# ---------------------------------------------------------------------------


class TestMaybeShowNotice:
    def test_imprime_na_primeira_chamada(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.delenv("BRASIL_MCP_TELEMETRY", raising=False)
        telemetry.maybe_show_notice()
        captured = capsys.readouterr()
        assert "Brasil MCP" in captured.err
        assert "BRASIL_MCP_TELEMETRY=1" in captured.err

    def test_nao_imprime_na_segunda_chamada(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.delenv("BRASIL_MCP_TELEMETRY", raising=False)
        telemetry.maybe_show_notice()
        capsys.readouterr()  # descarta primeiro output
        telemetry.maybe_show_notice()
        captured = capsys.readouterr()
        assert captured.err == ""

    def test_nao_imprime_quando_opt_in(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setenv("BRASIL_MCP_TELEMETRY", "1")
        telemetry.maybe_show_notice()
        captured = capsys.readouterr()
        assert captured.err == ""


# ---------------------------------------------------------------------------
# installation_id
# ---------------------------------------------------------------------------


class TestInstallationId:
    def test_persiste_entre_chamadas(self, tmp_path: Path) -> None:
        id1 = telemetry._get_or_create_installation_id()
        id2 = telemetry._get_or_create_installation_id()
        assert id1 == id2
        # Arquivo foi escrito no diretório isolado.
        assert (tmp_path / "brasil-mcp" / "installation_id").exists()


# ---------------------------------------------------------------------------
# track context manager
# ---------------------------------------------------------------------------


class TestTrackContextManager:
    def test_sucesso_chama_track_tool_call(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls: list[dict] = []

        def fake_track(
            tool: str,
            success: bool,
            latency_ms: float,
            error_code: str | None = None,
        ) -> None:
            calls.append(
                {
                    "tool": tool,
                    "success": success,
                    "latency_ms": latency_ms,
                    "error_code": error_code,
                }
            )

        monkeypatch.setattr(telemetry, "track_tool_call", fake_track)

        with telemetry.track("validate_cpf"):
            pass

        assert len(calls) == 1
        assert calls[0]["tool"] == "validate_cpf"
        assert calls[0]["success"] is True
        assert calls[0]["error_code"] is None
        assert calls[0]["latency_ms"] >= 0

    def test_excecao_propaga_e_registra_falha(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls: list[dict] = []

        def fake_track(
            tool: str,
            success: bool,
            latency_ms: float,
            error_code: str | None = None,
        ) -> None:
            calls.append(
                {
                    "tool": tool,
                    "success": success,
                    "error_code": error_code,
                }
            )

        monkeypatch.setattr(telemetry, "track_tool_call", fake_track)

        with pytest.raises(ValueError, match="boom"):
            with telemetry.track("validate_cpf"):
                raise ValueError("boom")

        assert len(calls) == 1
        assert calls[0]["tool"] == "validate_cpf"
        assert calls[0]["success"] is False
        assert calls[0]["error_code"] == "ValueError"


# ---------------------------------------------------------------------------
# regression: módulo importável sem posthog instalado
# ---------------------------------------------------------------------------


def test_modulo_importavel_sem_posthog_instalado() -> None:
    # Apenas re-importar para garantir que o import top-level não exige posthog.
    importlib.reload(telemetry)
