"""Cálculos do resumo (funções puras sobre a lista de eventos)."""
from __future__ import annotations

import datetime as dt
from collections import Counter
from dataclasses import dataclass

from .historico import Evento

DIAS_SEMANA = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
MIN_EVENTOS_INSIGHT = 3


@dataclass(frozen=True)
class Resumo:
    hoje: int
    ontem_ate_agora: int
    por_hora: list[int]                    # 24 posições, hoje
    ultimos_7: list[tuple[str, int]]       # (rótulo do dia, alertas), do mais antigo para hoje
    apps: list[tuple[str, int]]            # últimos 7 dias, do mais frequente para o menos
    total_semana: int
    insight: str


def calcular_resumo(eventos: list[Evento], agora: dt.datetime) -> Resumo:
    hoje, ontem = agora.date(), agora.date() - dt.timedelta(days=1)
    semana = [e for e in eventos if 0 <= (hoje - e.quando.date()).days < 7]

    por_hora = [0] * 24
    for e in eventos:
        if e.quando.date() == hoje:
            por_hora[e.quando.hour] += 1

    por_dia = Counter(e.quando.date() for e in semana)
    dias = [hoje - dt.timedelta(days=i) for i in range(6, -1, -1)]
    ultimos_7 = [("hoje" if d == hoje else DIAS_SEMANA[d.weekday()], por_dia[d]) for d in dias]

    ontem_ate_agora = sum(1 for e in eventos if e.quando.date() == ontem and e.quando.time() <= agora.time())
    apps = Counter(e.app for e in semana).most_common()
    return Resumo(
        hoje=sum(por_hora),
        ontem_ate_agora=ontem_ate_agora,
        por_hora=por_hora,
        ultimos_7=ultimos_7,
        apps=apps,
        total_semana=len(semana),
        insight=gerar_insight(semana, apps),
    )


def janela_de_pico(horas: Counter, largura: int = 2) -> int:
    """Hora de início da janela de `largura` horas com mais alertas."""
    return max(range(24), key=lambda h: sum(horas[(h + i) % 24] for i in range(largura)))


def gerar_insight(semana: list[Evento], apps: list[tuple[str, int]]) -> str:
    if len(semana) < MIN_EVENTOS_INSIGHT:
        return "Ainda há poucos alertas para achar um padrão. Continue usando."
    app, n = apps[0]
    inicio = janela_de_pico(Counter(e.quando.hour for e in semana))
    pct = round(100 * n / len(semana))
    return f"{pct}% dos alertas dos últimos 7 dias foram no {app}. O pico é entre {inicio}h e {(inicio + 2) % 24}h."


def formatar_duracao(segundos: float) -> str:
    minutos = int(segundos // 60)
    if minutos < 1:
        return "< 1 min"
    h, m = divmod(minutos, 60)
    return f"{h}h {m:02d}min" if h else f"{m} min"
