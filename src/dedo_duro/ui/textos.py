"""Textos da interface (um lugar só, usados pela janela e pela bandeja)."""
from __future__ import annotations

from ..dados.resumo import formatar_duracao
from ..monitor import Estado

TITULO_ESTADO = {
    Estado.VIGIANDO: "Vigiando",
    Estado.PAUSADO: "Pausado",
    Estado.EM_CHAMADA: "Em chamada",
    Estado.CAMERA_OCUPADA: "Câmera ocupada",
}


def alertas_hoje(n: int) -> str:
    return f"{n} {'alerta' if n == 1 else 'alertas'} hoje"


def detalhe_estado(estado: Estado, sem_alerta_s: float, app_em_chamada: str | None) -> str:
    return {
        Estado.VIGIANDO: f"Sem alerta há {formatar_duracao(sem_alerta_s)}",
        Estado.PAUSADO: "Clique em Retomar para voltar a vigiar",
        Estado.EM_CHAMADA: f"Pausado enquanto {app_em_chamada} usa câmera/microfone",
        Estado.CAMERA_OCUPADA: "Outro app está usando a câmera",
    }[estado]


def status_curto(estado: Estado, n_alertas: int, app_em_chamada: str | None) -> str:
    titulo = f"Pausado: em chamada ({app_em_chamada})" if estado is Estado.EM_CHAMADA else TITULO_ESTADO[estado]
    return f"{titulo} · {alertas_hoje(n_alertas)}"
