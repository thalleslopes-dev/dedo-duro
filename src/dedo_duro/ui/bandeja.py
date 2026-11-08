"""Ícone na bandeja do Windows. Os cliques viram tarefas numa fila, executadas na thread do Tk."""
from __future__ import annotations

import queue
import threading
from collections.abc import Callable
from dataclasses import dataclass

import pystray
from PIL import Image, ImageDraw, ImageOps

from .. import NOME
from ..monitor import Estado
from .tema import COR, LOGO_PNG

TAMANHO = 64


def imagem_do_estado(estado: Estado) -> Image.Image:
    """Mascote normal (vigiando), cinza (pausado) ou com bolinha laranja (em chamada / câmera ocupada)."""
    img = Image.open(LOGO_PNG).convert("RGBA").resize((TAMANHO, TAMANHO), Image.LANCZOS)
    if estado is Estado.PAUSADO:
        cinza = ImageOps.grayscale(img).convert("RGBA")
        cinza.putalpha(img.getchannel("A"))
        return cinza
    if estado in (Estado.EM_CHAMADA, Estado.CAMERA_OCUPADA):
        d = ImageDraw.Draw(img)
        d.ellipse([TAMANHO - 26, TAMANHO - 26, TAMANHO - 1, TAMANHO - 1], fill="#FFFFFF")
        d.ellipse([TAMANHO - 22, TAMANHO - 22, TAMANHO - 5, TAMANHO - 5], fill=COR["laranja"])
    return img


@dataclass
class AcoesBandeja:
    resumo: Callable[[], None]
    pausar: Callable[[], None]
    testar_alerta: Callable[[], None]
    alternar_executar_ao_ligar: Callable[[], None]
    sair: Callable[[], None]
    status: Callable[[], str]
    pausado: Callable[[], bool]
    executar_ao_ligar: Callable[[], bool]


class Bandeja:
    def __init__(self, acoes: AcoesBandeja, fila: queue.Queue):
        self._fila = fila
        self._imagens = {e: imagem_do_estado(e) for e in Estado}
        self._estado = Estado.VIGIANDO
        na_fila = self._na_fila
        menu = pystray.Menu(
            pystray.MenuItem(lambda item: acoes.status(), None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Ver resumo", na_fila(acoes.resumo), default=True),
            pystray.MenuItem(lambda item: "Retomar" if acoes.pausado() else "Pausar", na_fila(acoes.pausar)),
            pystray.MenuItem("Testar alerta", na_fila(acoes.testar_alerta)),
            pystray.MenuItem("Executar quando o computador ligar", na_fila(acoes.alternar_executar_ao_ligar),
                             checked=lambda item: acoes.executar_ao_ligar()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Sair", na_fila(acoes.sair)),
        )
        self._icone = pystray.Icon("dedo_duro", self._imagens[self._estado], NOME, menu)

    def _na_fila(self, funcao: Callable[[], None]):
        return lambda icon, item: self._fila.put(funcao)

    def iniciar(self) -> None:
        threading.Thread(target=self._icone.run, daemon=True, name="bandeja").start()

    def atualizar(self, estado: Estado, dica: str) -> None:
        if estado is not self._estado:
            self._estado = estado
            self._icone.icon = self._imagens[estado]
        dica = f"{NOME} · {dica}"[:120]
        if self._icone.title != dica:
            self._icone.title = dica

    def parar(self) -> None:
        self._icone.stop()
