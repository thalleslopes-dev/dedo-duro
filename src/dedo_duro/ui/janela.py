"""Janela de controle: fica minimizada na barra de tarefas e abre centralizada."""
from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass
from tkinter import ttk

from .. import NOME
from ..monitor import Estado
from . import textos
from .tema import COR, icone, logo

COR_ESTADO = {
    Estado.VIGIANDO: COR["verde"],
    Estado.PAUSADO: COR["terciario"],
    Estado.EM_CHAMADA: COR["laranja"],
    Estado.CAMERA_OCUPADA: COR["laranja"],
}


@dataclass
class Acoes:
    resumo: Callable[[], None]
    pausar: Callable[[], None]
    sair: Callable[[], None]
    executar_ao_ligar: Callable[[bool], None]


class JanelaControle:
    def __init__(self, root: tk.Tk, escala: float, acoes: Acoes, executar_ao_ligar: bool):
        self.root = root
        self.escala = escala
        px = self.px
        root.title(NOME)
        root.configure(bg=COR["fundo"])
        root.resizable(False, False)
        root.minsize(px(440), 0)
        root.protocol("WM_DELETE_WINDOW", root.iconify)  # fechar = minimizar

        self._img = {
            "logo": logo(px(76)),
            "grafico": icone("grafico", px(24), COR["texto"]),
            "pausa": icone("pausa", px(24), COR["texto"]),
            "play": icone("play", px(24), COR["texto"]),
            "sair": icone("sair", px(24), COR["vermelho"]),
        }
        corpo = tk.Frame(root, bg=COR["fundo"], padx=px(24), pady=px(24))
        corpo.pack(fill="both", expand=True)
        self._montar_topo(corpo)
        self._montar_botoes(corpo, acoes)
        self._montar_opcoes(corpo, acoes, executar_ao_ligar)

        # o Windows ignora a posição de janelas que começam minimizadas: centraliza ao restaurar
        self._centralizada = False
        root.bind("<Map>", self._centralizar_uma_vez)
        root.iconify()

    def px(self, v: float) -> int:
        return int(v * self.escala)

    def _montar_topo(self, pai: tk.Frame) -> None:
        px, bg = self.px, COR["fundo"]
        topo = tk.Frame(pai, bg=bg)
        topo.pack(fill="x")
        tk.Label(topo, image=self._img["logo"], bg=bg).pack(side="left", padx=(0, px(18)))
        textos_frame = tk.Frame(topo, bg=bg)
        textos_frame.pack(side="left", fill="x")
        linha = tk.Frame(textos_frame, bg=bg)
        linha.pack(anchor="w")
        self._ponto = tk.Label(linha, text="●", font=("Segoe UI", 11), bg=bg)  # cor + texto: nunca só cor
        self._ponto.pack(side="left", padx=(0, px(6)))
        self._estado = tk.Label(linha, font=("Segoe UI Semibold", 17), fg=COR["texto"], bg=bg)
        self._estado.pack(side="left")
        self._contagem = tk.Label(textos_frame, font=("Segoe UI", 11), fg=COR["texto"], bg=bg)
        self._contagem.pack(anchor="w", pady=(px(2), 0))
        self._detalhe = tk.Label(textos_frame, font=("Segoe UI", 9), fg=COR["secundario"], bg=bg)
        self._detalhe.pack(anchor="w")

    def _montar_botoes(self, pai: tk.Frame, acoes: Acoes) -> None:
        botoes = tk.Frame(pai, bg=COR["fundo"])
        botoes.pack(fill="x", pady=(self.px(22), 0))
        for col in range(3):
            botoes.columnconfigure(col, weight=1, uniform="botoes")
        self._botao(botoes, 0, "grafico", "Resumo", acoes.resumo)
        self._btn_pausa = self._botao(botoes, 1, "pausa", "Pausar", acoes.pausar)
        self._botao(botoes, 2, "sair", "Sair", acoes.sair, cor=COR["vermelho"])

    def _montar_opcoes(self, pai: tk.Frame, acoes: Acoes, executar_ao_ligar: bool) -> None:
        estilo = ttk.Style(self.root)
        estilo.configure("Opcao.TCheckbutton", background=COR["fundo"], foreground=COR["texto"],
                         font=("Segoe UI", 10))
        self._var_ao_ligar = tk.BooleanVar(value=executar_ao_ligar)
        ttk.Checkbutton(pai, text="Executar quando o computador ligar", style="Opcao.TCheckbutton",
                        variable=self._var_ao_ligar, cursor="hand2",
                        command=lambda: acoes.executar_ao_ligar(self._var_ao_ligar.get()),
                        ).pack(anchor="w", padx=self.px(5), pady=(self.px(18), 0))

    def definir_executar_ao_ligar(self, valor: bool) -> None:
        """Sincroniza o checkbox quando a opção muda por outro lugar (menu da bandeja)."""
        self._var_ao_ligar.set(valor)

    def _botao(self, pai, coluna, nome_icone, texto, comando, cor=None) -> tk.Label:
        b = tk.Label(pai, image=self._img[nome_icone], text=texto, compound="top", font=("Segoe UI", 10),
                     fg=cor or COR["texto"], bg=COR["cartao"], cursor="hand2", pady=self.px(14))
        b.grid(row=0, column=coluna, sticky="nsew", padx=self.px(5))
        b.bind("<Button-1>", lambda e: comando())
        b.bind("<Enter>", lambda e: b.config(bg=COR["hover"]))
        b.bind("<Leave>", lambda e: b.config(bg=COR["cartao"]))
        return b

    def _centralizar_uma_vez(self, evento) -> None:
        if self._centralizada or evento.widget is not self.root or self.root.state() != "normal":
            return
        self._centralizada = True
        self.root.update_idletasks()
        w, h = self.root.winfo_width(), self.root.winfo_height()
        self.root.geometry(f"+{(self.root.winfo_screenwidth() - w) // 2}+{(self.root.winfo_screenheight() - h) // 2}")

    def atualizar(self, estado: Estado, n_alertas: int, sem_alerta_s: float, app_em_chamada: str | None) -> None:
        pausado = estado is Estado.PAUSADO
        self._ponto.config(fg=COR_ESTADO[estado])
        self._estado.config(text=textos.TITULO_ESTADO[estado])
        self._contagem.config(text=textos.alertas_hoje(n_alertas))
        self._detalhe.config(text=textos.detalhe_estado(estado, sem_alerta_s, app_em_chamada))
        self._btn_pausa.config(image=self._img["play" if pausado else "pausa"], text="Retomar" if pausado else "Pausar")
