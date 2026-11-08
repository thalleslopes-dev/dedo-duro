"""Janela de resumo: hoje vs. ontem, recorde, gatilhos (horários e apps). Só desenha; os números vêm prontos."""
from __future__ import annotations

import datetime as dt
import tkinter as tk

from ..dados.resumo import Resumo, formatar_duracao
from .tema import COR, icone

DIAS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro",
         "outubro", "novembro", "dezembro"]
LARGURA = 540
MARGEM = 24
SEM_DADOS = "Nenhum alerta neste período"


def _ret_arred(c: tk.Canvas, x0, y0, x1, y1, r, **kw):
    r = max(0, min(r, (x1 - x0) / 2, (y1 - y0) / 2))
    pts = [x0 + r, y0, x1 - r, y0, x1, y0, x1, y0 + r, x1, y1 - r, x1, y1, x1 - r, y1, x0 + r, y1,
           x0, y1, x0, y1 - r, x0, y0 + r, x0, y0]
    return c.create_polygon(pts, smooth=True, **kw)


def _plural(v: int) -> str:
    return f"{v} {'alerta' if v == 1 else 'alertas'}"


class JanelaResumo:
    def __init__(self, root: tk.Misc, escala: float, resumo: Resumo, recorde_s: float, hoje: dt.date):
        self.e = escala
        self.r = resumo
        self.recorde_s = recorde_s
        self.hoje = hoje
        self.top = tk.Toplevel(root, bg=COR["fundo"])
        self.top.title("Resumo · Dedo-Duro")
        self.top.resizable(False, False)
        self.top.attributes("-topmost", True)
        self.top.after(300, lambda: self.top.attributes("-topmost", False))
        self._icones: dict = {}
        self._tooltip: list[int] = []
        self.c = tk.Canvas(self.top, bg=COR["fundo"], highlightthickness=0, width=self.px(LARGURA))
        self.c.pack()
        self.c.config(height=self._desenhar())

    def px(self, v: float) -> int:
        return int(v * self.e)

    def _icone(self, nome: str, tam: int, cor: str):
        chave = (nome, tam, cor)
        if chave not in self._icones:
            self._icones[chave] = icone(nome, self.px(tam), cor)
        return self._icones[chave]

    def _cartao(self, y: int, altura: int) -> None:
        _ret_arred(self.c, self.px(MARGEM), y, self.px(LARGURA - MARGEM), y + altura, self.px(14),
                   fill=COR["cartao"], outline="")

    def _titulo_secao(self, y: int, texto: str) -> None:
        self.c.create_text(self.px(40), y, text=texto, anchor="nw", font=("Segoe UI Semibold", 10), fill=COR["texto"])

    # ------------------------------------------------------------ layout
    def _desenhar(self) -> int:
        px = self.px
        self.c.create_text(px(MARGEM), px(22), text="Resumo", anchor="nw", font=("Segoe UI Semibold", 20),
                           fill=COR["texto"])
        self.c.create_text(px(MARGEM), px(60), anchor="nw", font=("Segoe UI", 10), fill=COR["secundario"],
                           text=f"{DIAS[self.hoje.weekday()]}, {self.hoje.day} de {MESES[self.hoje.month - 1]}")
        y = px(96)
        for secao in (self._blocos, self._insight, self._grafico_horas, self._grafico_dias, self._apps):
            y = secao(y) + px(14)
        return y + px(10)

    def _comparacao(self) -> tuple[str, str | None, str | None]:
        hoje, ontem = self.r.hoje, self.r.ontem_ate_agora
        if hoje < ontem:
            return f"{ontem - hoje} a menos que ontem", "desceu", COR["verde"]
        if hoje > ontem:
            return f"{hoje - ontem} a mais que ontem", "subiu", COR["vermelho"]
        return "igual a ontem", None, None

    def _blocos(self, y: int) -> int:
        px = self.px
        gap, alt = px(12), px(96)
        larg = (px(LARGURA) - 2 * px(MARGEM) - 2 * gap) / 3
        comp, ic, cor = self._comparacao()
        blocos = [
            ("Hoje", str(self.r.hoje), "alerta" if self.r.hoje == 1 else "alertas", None, None),
            ("Ontem até agora", str(self.r.ontem_ate_agora), comp, ic, cor),
            ("Recorde sem alerta", formatar_duracao(self.recorde_s), "hoje, vigiando", None, None),
        ]
        for i, (rotulo, valor, sub, ic, cor) in enumerate(blocos):
            x0 = px(MARGEM) + i * (larg + gap)
            _ret_arred(self.c, x0, y, x0 + larg, y + alt, px(14), fill=COR["cartao"], outline="")
            self.c.create_text(x0 + px(14), y + px(12), text=rotulo, anchor="nw", font=("Segoe UI", 9),
                               fill=COR["secundario"])
            self.c.create_text(x0 + px(14), y + px(30), text=valor, anchor="nw",
                               font=("Segoe UI Semibold", 24 if len(valor) <= 4 else 16), fill=COR["texto"])
            xs = x0 + px(14)
            if ic:  # seta + texto: o significado nunca depende só da cor
                self.c.create_image(xs, y + px(78), image=self._icone(ic, 14, cor), anchor="w")
                xs += px(16)
            self.c.create_text(xs, y + px(78), text=sub, anchor="w", font=("Segoe UI", 8), fill=COR["secundario"])
        return y + alt

    def _insight(self, y: int) -> int:
        px = self.px
        m = px(MARGEM)
        texto = self.c.create_text(m + px(48), y + px(16), text=self.r.insight, anchor="nw",
                                   width=px(LARGURA) - 2 * m - px(64), font=("Segoe UI", 10), fill=COR["texto"])
        alt = (self.c.bbox(texto)[3] - y) + px(16)
        fundo = _ret_arred(self.c, m, y, px(LARGURA) - m, y + alt, px(14), fill=COR["azul_suave"], outline="")
        self.c.tag_lower(fundo)
        self.c.create_image(m + px(16), y + px(14), image=self._icone("ideia", 20, COR["azul"]), anchor="nw")
        return y + alt

    def _barras(self, y_topo, rotulos, valores, mostrar_rotulo, destacar=None, formato_tip=None, alt=110) -> None:
        """Barras verticais de uma série. Valor escrito só na barra destacada; o resto aparece no hover."""
        px = self.px
        x0, x1 = px(44), px(LARGURA - 44)
        base = y_topo + px(alt)
        maximo = max(valores, default=0)
        passo = (x1 - x0) / len(valores)
        larg = min(passo * 0.62, px(28))
        self.c.create_line(x0, base, x1, base, fill=COR["divisor"])
        if not maximo:
            self.c.create_text((x0 + x1) / 2, base - px(alt) / 2, text=SEM_DADOS, font=("Segoe UI", 9),
                               fill=COR["terciario"])
        for i, (rotulo, v) in enumerate(zip(rotulos, valores, strict=True)):
            cx = x0 + passo * (i + 0.5)
            if v:
                topo = base - (px(alt) - px(14)) * v / maximo
                r = min(px(4), larg / 2)
                _ret_arred(self.c, cx - larg / 2, topo, cx + larg / 2, base, r, fill=COR["azul"], outline="")
                self.c.create_rectangle(cx - larg / 2, base - r, cx + larg / 2, base, fill=COR["azul"], outline="")
                if i == destacar:
                    self.c.create_text(cx, topo - px(4), text=str(v), anchor="s", font=("Segoe UI Semibold", 8),
                                       fill=COR["texto"])
            if mostrar_rotulo(i):
                self.c.create_text(cx, base + px(6), text=rotulo, anchor="n", font=("Segoe UI", 8),
                                   fill=COR["secundario"])
            alvo = self.c.create_rectangle(cx - passo / 2, y_topo, cx + passo / 2, base, fill="", outline="")
            dica = formato_tip(rotulo, v) if formato_tip else f"{rotulo}: {v}"
            self.c.tag_bind(alvo, "<Enter>", lambda e, t=dica, x=cx: self._mostrar_tip(x, y_topo, t))
            self.c.tag_bind(alvo, "<Leave>", lambda e: self._esconder_tip())

    def _grafico_horas(self, y: int) -> int:
        alt = self.px(186)
        self._cartao(y, alt)
        self._titulo_secao(y + self.px(14), "Hoje, por hora")
        self._barras(y + self.px(42), [f"{h}h" for h in range(24)], self.r.por_hora, lambda i: i % 3 == 0,
                     destacar=dt.datetime.now().hour,
                     formato_tip=lambda rot, v: f"{rot}–{int(rot[:-1]) + 1}h · {_plural(v)}")
        return y + alt

    def _grafico_dias(self, y: int) -> int:
        alt = self.px(186)
        self._cartao(y, alt)
        self._titulo_secao(y + self.px(14), "Últimos 7 dias")
        self._barras(y + self.px(42), [r for r, _ in self.r.ultimos_7], [v for _, v in self.r.ultimos_7],
                     lambda i: True, destacar=6, formato_tip=lambda rot, v: f"{rot} · {_plural(v)}")
        return y + alt

    def _apps(self, y: int) -> int:
        px = self.px
        apps = self.r.apps[:5]
        linha = px(30)
        alt = px(48) + max(1, len(apps)) * linha + px(8)
        self._cartao(y, alt)
        self._titulo_secao(y + px(14), "Onde acontece · últimos 7 dias")
        if not apps:
            self.c.create_text(px(LARGURA) / 2, y + px(60), text=SEM_DADOS, font=("Segoe UI", 9),
                               fill=COR["terciario"])
            return y + alt
        x_barra, x_fim = px(150), px(LARGURA - 110)
        maior = apps[0][1]
        for i, (app, n) in enumerate(apps):
            cy = y + px(56) + i * linha
            self.c.create_text(px(40), cy, text=app, anchor="w", font=("Segoe UI", 9), fill=COR["texto"])
            _ret_arred(self.c, x_barra, cy - px(4), x_fim, cy + px(4), px(4), fill=COR["fundo"], outline="")
            fim = max(x_barra + (x_fim - x_barra) * n / maior, x_barra + px(8))
            _ret_arred(self.c, x_barra, cy - px(4), fim, cy + px(4), px(4), fill=COR["azul"], outline="")
            self.c.create_text(px(LARGURA - 40), cy, anchor="e", font=("Segoe UI", 9), fill=COR["secundario"],
                               text=f"{n} · {round(100 * n / self.r.total_semana)}%")
        return y + alt

    # ------------------------------------------------------------ tooltip
    def _mostrar_tip(self, x: float, y: float, texto: str) -> None:
        self._esconder_tip()
        px = self.px
        t = self.c.create_text(x, y - px(2), text=texto, anchor="s", font=("Segoe UI Semibold", 8), fill="#FFFFFF")
        x0, y0, x1, y1 = self.c.bbox(t)
        dx = max(0, px(30) - (x0 - px(8))) - max(0, (x1 + px(8)) - px(LARGURA - 30))  # não sai da janela
        self.c.move(t, dx, 0)
        fundo = _ret_arred(self.c, x0 - px(8) + dx, y0 - px(4), x1 + px(8) + dx, y1 + px(4), px(6),
                           fill=COR["texto"], outline="")
        self.c.tag_raise(t, fundo)
        self._tooltip = [t, fundo]

    def _esconder_tip(self) -> None:
        for item in self._tooltip:
            self.c.delete(item)
        self._tooltip = []
