"""Testes para as ferramentas de calendário brasileiro."""

from __future__ import annotations

from brasil_mcp.core.calendar.feriados import (
    contar_dias_uteis,
    is_feriado_nacional,
    listar_feriados,
    proximo_dia_util,
)

# ---------------------------------------------------------------------------
# is_feriado_nacional
# ---------------------------------------------------------------------------


class TestIsFeriadoNacional:
    def test_independencia_eh_nacional(self) -> None:
        result = is_feriado_nacional("2026-09-07")
        assert result["is_feriado"] is True
        assert result["esfera"] == "nacional"
        assert "Independência" in result["nome"]
        assert result["raw_date"] == "2026-09-07"

    def test_quarta_normal_nao_eh_feriado(self) -> None:
        result = is_feriado_nacional("2026-08-12")
        assert result["is_feriado"] is False
        assert result["nome"] is None
        assert result["esfera"] is None

    def test_natal_eh_feriado_nacional(self) -> None:
        result = is_feriado_nacional("2026-12-25")
        assert result["is_feriado"] is True
        assert result["esfera"] == "nacional"
        assert "Natal" in result["nome"]

    def test_revolucao_constitucionalista_sp_eh_estadual(self) -> None:
        # 2026-07-09 — Revolução Constitucionalista, feriado estadual de SP
        # (probe confirmou que está presente no holidays lib para subdiv='SP').
        result = is_feriado_nacional("2026-07-09", uf="SP")
        assert result["is_feriado"] is True
        assert result["esfera"] == "estadual"
        assert result["nome"] is not None

    def test_estadual_sem_uf_nao_eh_detectado(self) -> None:
        # Mesma data sem uf="SP" — não deve ser detectada.
        result = is_feriado_nacional("2026-07-09")
        assert result["is_feriado"] is False

    def test_municipio_param_aceito_mas_ignorado(self) -> None:
        # Aceita o argumento, sem alterar comportamento em v0.1.0.
        result = is_feriado_nacional("2026-08-12", municipio="São Paulo")
        assert result["is_feriado"] is False


# ---------------------------------------------------------------------------
# proximo_dia_util
# ---------------------------------------------------------------------------


class TestProximoDiaUtil:
    def test_sexta_normal_pula_fim_de_semana(self) -> None:
        # 2026-05-22 é uma sexta-feira; próximo útil é segunda 2026-05-25.
        result = proximo_dia_util("2026-05-22")
        assert result["date"] == "2026-05-25"
        assert result["dias_pulados"] == 3

    def test_sexta_antes_de_feriado_segunda(self) -> None:
        # 2026-09-04 (sexta); 09-07 é Independência (segunda).
        # Sem include_today, avança 1; sat, sun, mon-feriado, ter → 2026-09-08.
        result = proximo_dia_util("2026-09-04")
        assert result["date"] == "2026-09-08"
        assert result["dias_pulados"] == 4

    def test_include_today_se_for_dia_util(self) -> None:
        # 2026-09-04 é sexta; com include_today=True, retorna o próprio dia.
        result = proximo_dia_util("2026-09-04", include_today=True)
        assert result["date"] == "2026-09-04"
        assert result["dias_pulados"] == 0

    def test_include_today_em_feriado_avança(self) -> None:
        # 2026-09-07 (Independência, segunda) com include_today=True;
        # deve avançar para 2026-09-08.
        result = proximo_dia_util("2026-09-07", include_today=True)
        assert result["date"] == "2026-09-08"
        assert result["dias_pulados"] == 1

    def test_uf_considera_feriado_estadual(self) -> None:
        # 2026-07-09 (Revolução Constitucionalista) é quinta-feira em SP.
        # Sem uf: include_today=True retorna a própria data.
        sem_uf = proximo_dia_util("2026-07-09", include_today=True)
        assert sem_uf["date"] == "2026-07-09"
        # Com uf="SP": é feriado estadual; deve avançar para sexta 2026-07-10.
        com_uf = proximo_dia_util("2026-07-09", uf="SP", include_today=True)
        assert com_uf["date"] == "2026-07-10"
        assert com_uf["dias_pulados"] == 1


# ---------------------------------------------------------------------------
# contar_dias_uteis
# ---------------------------------------------------------------------------


class TestContarDiasUteis:
    def test_setembro_2026_inclui_independencia(self) -> None:
        # De 2026-09-01 (terça) a 2026-09-30 (quarta), exclusive end.
        # Setembro 2026: 1=ter, 7=seg feriado, 30=qua.
        # Dias úteis úteis no intervalo [01, 30): contar manualmente.
        # Datas 01..29 (29 dias). Pulamos 5,6,12,13,19,20,26,27 (fins-de-semana) = 8.
        # Pulamos 7 (feriado nacional). 29 - 8 - 1 = 20.
        result = contar_dias_uteis("2026-09-01", "2026-09-30")
        assert result["count"] == 20
        assert result["total_dias"] == 29
        assert any(
            f["date"] == "2026-09-07" and "Independência" in f["nome"]
            for f in result["feriados_no_periodo"]
        )

    def test_inclusive_end_conta_dia_util(self) -> None:
        # 2026-09-28 (segunda) a 2026-09-29 (terça), inclusive_end=True
        # → 2 dias úteis.
        result = contar_dias_uteis("2026-09-28", "2026-09-29", inclusive_end=True)
        assert result["count"] == 2
        assert result["total_dias"] == 2

    def test_exclusive_end_nao_conta_ultimo_dia(self) -> None:
        # Mesma janela sem inclusive_end → só 2026-09-28 conta.
        result = contar_dias_uteis("2026-09-28", "2026-09-29")
        assert result["count"] == 1
        assert result["total_dias"] == 1

    def test_uf_adiciona_feriado_estadual_a_lista(self) -> None:
        # 2026-07-01 a 2026-07-31 inclui 2026-07-09 (Revolução Const.) em SP.
        result = contar_dias_uteis("2026-07-01", "2026-07-31", uf="SP")
        names = [f["date"] for f in result["feriados_no_periodo"]]
        assert "2026-07-09" in names

    def test_periodo_sem_feriados(self) -> None:
        # 2026-08-03 (seg) a 2026-08-08 (sáb), exclusive end.
        # 5 dias, todos úteis (seg-sex).
        result = contar_dias_uteis("2026-08-03", "2026-08-08")
        assert result["count"] == 5
        assert result["feriados_no_periodo"] == []


# ---------------------------------------------------------------------------
# listar_feriados
# ---------------------------------------------------------------------------


class TestListarFeriados:
    def test_nacional_2026_tem_dez_ou_mais(self) -> None:
        result = listar_feriados(2026)
        assert result["ano"] == 2026
        assert result["uf"] is None
        assert len(result["feriados"]) >= 10
        for f in result["feriados"]:
            assert f["esfera"] == "nacional"

    def test_sp_inclui_estadual_e_nacional(self) -> None:
        result = listar_feriados(2026, uf="SP")
        assert result["uf"] == "SP"
        esferas = {f["esfera"] for f in result["feriados"]}
        assert "nacional" in esferas
        assert "estadual" in esferas
        # 2026-07-09 deve estar marcado como estadual.
        sp_estadual = [f for f in result["feriados"] if f["esfera"] == "estadual"]
        assert any(f["date"] == "2026-07-09" for f in sp_estadual)

    def test_ordenado_por_data(self) -> None:
        result = listar_feriados(2026, uf="SP")
        dates = [f["date"] for f in result["feriados"]]
        assert dates == sorted(dates)

    def test_sem_uf_nao_inclui_estadual(self) -> None:
        result = listar_feriados(2026)
        assert all(f["esfera"] == "nacional" for f in result["feriados"])
        # 2026-07-09 não deve aparecer (é estadual SP).
        assert not any(f["date"] == "2026-07-09" for f in result["feriados"])
