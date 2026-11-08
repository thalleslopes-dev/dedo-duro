"""Regras de quando e como alertar. Sem câmera e sem interface: recebe fatos e um relógio, devolve decisões."""
from __future__ import annotations

from enum import Enum

from .config import Config

MAX_SALTO_S = 5.0  # ignora saltos de tempo maiores (ex.: notebook suspenso)


class TipoAlerta(str, Enum):
    DISCRETO = "discreto"
    TELA_CHEIA = "tela_cheia"


class Estado(str, Enum):
    VIGIANDO = "vigiando"
    PAUSADO = "pausado"
    EM_CHAMADA = "em_chamada"
    CAMERA_OCUPADA = "camera_ocupada"


class Monitor:
    def __init__(self, cfg: Config, recorde_s: float = 0.0):
        self.cfg = cfg
        self.seguidos = 0                     # quadros seguidos com mão na boca
        self.ultimo_alerta: float | None = None
        self.sem_alerta_s = 0.0               # tempo vigiando desde o último alerta
        self.recorde_s = recorde_s            # maior tempo vigiando sem alerta, hoje

    def registrar_quadro(self, na_boca: bool, agora: float) -> TipoAlerta | None:
        """Registra o resultado de um quadro. Devolve o tipo de alerta a disparar, ou None."""
        self.seguidos = self.seguidos + 1 if na_boca else 0
        if self.seguidos < self.cfg.seguidos:
            return None
        desde_ultimo = None if self.ultimo_alerta is None else agora - self.ultimo_alerta
        if desde_ultimo is not None and desde_ultimo < self.cfg.espera:
            return None
        # progressivo: o primeiro é discreto; repetiu dentro da janela -> tela cheia
        repetiu = desde_ultimo is not None and desde_ultimo < self.cfg.repeticao
        self.ultimo_alerta = agora
        self.sem_alerta_s = 0.0
        return TipoAlerta.TELA_CHEIA if (self.cfg.sempre_tela_cheia or repetiu) else TipoAlerta.DISCRETO

    def contar_tempo(self, decorrido: float, vigiando: bool) -> None:
        """Soma tempo sem alerta (só enquanto está de fato vigiando) e atualiza o recorde."""
        if not vigiando or decorrido <= 0:
            return
        self.sem_alerta_s += min(decorrido, MAX_SALTO_S)
        self.recorde_s = max(self.recorde_s, self.sem_alerta_s)

    def novo_dia(self) -> None:
        self.sem_alerta_s = 0.0
        self.recorde_s = 0.0
