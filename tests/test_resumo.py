import datetime as dt
from collections import Counter

from dedo_duro.dados.historico import Evento
from dedo_duro.dados.resumo import calcular_resumo, formatar_duracao, janela_de_pico

AGORA = dt.datetime(2026, 11, 8, 16, 0)  # domingo


def _ev(dias_atras: int, hora: int, app: str = "Slack") -> Evento:
    return Evento(dt.datetime.combine(AGORA.date() - dt.timedelta(days=dias_atras), dt.time(hora)), app, "discreto")


def test_contagens_de_hoje_e_ontem_ate_agora():
    eventos = [_ev(0, 9), _ev(0, 15), _ev(1, 10), _ev(1, 20)]  # ontem às 20h ainda não "chegou"
    r = calcular_resumo(eventos, AGORA)
    assert r.hoje == 2
    assert r.ontem_ate_agora == 1
    assert r.por_hora[9] == 1 and r.por_hora[15] == 1


def test_ultimos_7_dias_rotulados_e_ordenados():
    r = calcular_resumo([_ev(0, 9), _ev(6, 9), _ev(7, 9)], AGORA)  # 7 dias atrás fica de fora
    assert [rot for rot, _ in r.ultimos_7] == ["seg", "ter", "qua", "qui", "sex", "sáb", "hoje"]
    assert r.ultimos_7[0][1] == 1 and r.ultimos_7[-1][1] == 1
    assert r.total_semana == 2


def test_ranking_de_apps_e_insight():
    eventos = [_ev(0, 15, "Slack")] * 3 + [_ev(1, 16, "Chrome")]
    r = calcular_resumo(eventos, AGORA)
    assert r.apps[0] == ("Slack", 3)
    assert "75% dos alertas" in r.insight and "Slack" in r.insight and "15h e 17h" in r.insight


def test_insight_com_poucos_dados():
    assert "poucos alertas" in calcular_resumo([_ev(0, 9)], AGORA).insight


def test_janela_de_pico_atravessa_meia_noite():
    assert janela_de_pico(Counter({23: 5, 0: 5, 12: 6})) == 23


def test_formatar_duracao():
    assert formatar_duracao(30) == "< 1 min"
    assert formatar_duracao(12 * 60) == "12 min"
    assert formatar_duracao(73 * 60) == "1h 13min"
