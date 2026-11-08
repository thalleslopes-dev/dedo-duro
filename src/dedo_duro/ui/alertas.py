"""Alertas estilo Apple: tela cheia (fundo escurecido + cartão central) e banner discreto no canto."""
from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from PIL import Image, ImageDraw, ImageFont, ImageTk

from .tema import COR, FONTE_TEXTO, FONTE_TITULO, icone_pil

SUPERSAMPLING = 3
_COR_CHAVE = "#010203"  # cor que vira transparente na janela (cantos arredondados)


def ordinal_hoje(n: int) -> str:
    return f"{n}ª vez hoje"


# ---------------------------------------------------------------- desenho
def _finalizar(img: Image.Image, cor_borda_fundo: tuple[int, int, int]) -> Image.Image:
    """Reduz o supersampling e pinta os cantos transparentes com a cor-chave."""
    img = img.resize((img.width // SUPERSAMPLING, img.height // SUPERSAMPLING), Image.LANCZOS)
    base = Image.new("RGBA", img.size, (*cor_borda_fundo, 255))
    base.alpha_composite(img)  # bordas semi-transparentes misturadas com a cor aproximada do fundo
    chave = Image.new("RGBA", img.size, _COR_CHAVE)
    mascara = img.getchannel("A").point(lambda a: 255 if a > 20 else 0)
    return Image.composite(base, chave, mascara).convert("RGB")


def desenhar_cartao_central(escala: float, vezes_hoje: int | None) -> Image.Image:
    u = escala * SUPERSAMPLING
    extra = 48 * u if vezes_hoje else 0
    largura, altura = int(300 * u), int(262 * u + extra)
    img = Image.new("RGBA", (largura, altura), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, largura - 1, altura - 1], radius=int(22 * u), fill=COR["cartao"])

    cx, r, topo = largura / 2, 34 * u, 30 * u
    d.ellipse([cx - r, topo, cx + r, topo + 2 * r], fill=COR["vermelho_suave"])
    ic = icone_pil("mao", int(38 * u), COR["vermelho"])
    img.alpha_composite(ic, (int(cx - ic.width / 2), int(topo + r - ic.height / 2)))

    d.text((cx, 120 * u), "Mão na boca", font=ImageFont.truetype(FONTE_TITULO, int(21 * u)),
           fill=COR["texto"], anchor="mt")
    if vezes_hoje:
        fonte = ImageFont.truetype(FONTE_TITULO, int(13 * u))
        texto = ordinal_hoje(vezes_hoje)
        larg, y0, alt = d.textlength(texto, font=fonte) + 28 * u, 154 * u, 28 * u
        d.rounded_rectangle([cx - larg / 2, y0, cx + larg / 2, y0 + alt], radius=int(alt / 2),
                            fill=COR["vermelho_suave"])
        d.text((cx, y0 + alt / 2), texto, font=fonte, fill=COR["vermelho"], anchor="mm")
    d.text((cx, 152 * u + extra), "Respira e solta a mão do rosto.",
           font=ImageFont.truetype(FONTE_TEXTO, int(14 * u)), fill=COR["secundario"], anchor="mt")

    y_div = altura - 50 * u
    d.line([0, y_div, largura, y_div], fill=COR["divisor"], width=max(1, int(u)))
    d.text((cx, y_div + 25 * u), "Ok", font=ImageFont.truetype(FONTE_TITULO, int(17 * u)),
           fill=COR["azul"], anchor="mm")
    return _finalizar(img, (40, 40, 42))


def desenhar_banner(escala: float, vezes_hoje: int | None) -> Image.Image:
    u = escala * SUPERSAMPLING
    largura, altura = int(320 * u), int(76 * u)
    img = Image.new("RGBA", (largura, altura), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, largura - 1, altura - 1], radius=int(18 * u), fill=COR["cartao"],
                        outline=COR["divisor"], width=max(1, int(u)))
    r, cx, cy = 22 * u, 38 * u, altura / 2
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=COR["vermelho_suave"])
    ic = icone_pil("mao", int(24 * u), COR["vermelho"])
    img.alpha_composite(ic, (int(cx - ic.width / 2), int(cy - ic.height / 2)))
    x = 74 * u
    d.text((x, 19 * u), "Mão na boca", font=ImageFont.truetype(FONTE_TITULO, int(15 * u)), fill=COR["texto"])
    sub = f"{ordinal_hoje(vezes_hoje)} · respira" if vezes_hoje else "Respira e solta a mão."
    d.text((x, 41 * u), sub, font=ImageFont.truetype(FONTE_TEXTO, int(13 * u)), fill=COR["secundario"])
    return _finalizar(img, (235, 235, 238))


# ---------------------------------------------------------------- janelas
Posicao = Callable[[int, int, int, int], tuple[int, int]]  # (tela_l, tela_a, l, a) -> (x, y)


class _Alerta:
    ESCURECER = 0.0  # opacidade do fundo preto em tela cheia (0 = sem fundo)

    def __init__(self, root: tk.Misc, imagem: Image.Image, posicao: Posicao, duracao_ms: int):
        self.root = root
        self._janelas: list[tk.Toplevel] = []
        self.fechando = False
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()

        if self.ESCURECER:
            self._fundo = self._nova_janela("black")
            self._fundo.geometry(f"{sw}x{sh}+0+0")
        self._cartao = self._nova_janela(_COR_CHAVE)
        self._cartao.attributes("-transparentcolor", _COR_CHAVE)
        self._img = ImageTk.PhotoImage(imagem)
        tk.Label(self._cartao, image=self._img, bg=_COR_CHAVE, bd=0, cursor="hand2").pack()
        x, y = posicao(sw, sh, self._img.width(), self._img.height())
        self._cartao.geometry(f"{self._img.width()}x{self._img.height()}+{x}+{y}")

        for janela in self._janelas:
            janela.bind("<Button-1>", lambda e: self.fechar())
        if self.ESCURECER:  # garante o cartão acima do fundo escurecido
            root.update_idletasks()
            self._cartao.lift(self._fundo)
            self._fundo.bind("<Map>", lambda e: self._cartao.lift(self._fundo))

        self._fade(0.0, 1.0)
        self._timer = root.after(duracao_ms, self.fechar)

    def _nova_janela(self, bg: str) -> tk.Toplevel:
        j = tk.Toplevel(self.root, bg=bg)
        j.overrideredirect(True)
        j.attributes("-topmost", True)
        j.attributes("-alpha", 0.0)
        self._janelas.append(j)
        return j

    def _fade(self, de: float, ate: float, passos: int = 10, i: int = 0, ao_terminar=None) -> None:
        v = de + (ate - de) * (i / passos)
        if ate > de:
            v = 1 - (1 - v) ** 3  # ease-out na entrada
        try:
            if self.ESCURECER:
                self._fundo.attributes("-alpha", self.ESCURECER * v)
            self._cartao.attributes("-alpha", v)
        except tk.TclError:
            return
        if i < passos:
            self.root.after(16, self._fade, de, ate, passos, i + 1, ao_terminar)
        elif ao_terminar:
            ao_terminar()

    def fechar(self) -> None:
        if self.fechando:
            return
        self.fechando = True
        self.root.after_cancel(self._timer)
        self._fade(1.0, 0.0, passos=20, ao_terminar=self._destruir)  # saída suave (~0,4 s)

    def _destruir(self) -> None:
        for janela in self._janelas:
            janela.destroy()


class AlertaTelaCheia(_Alerta):
    ESCURECER = 0.45

    def __init__(self, root: tk.Misc, escala: float, duracao_ms: int, vezes_hoje: int | None):
        super().__init__(root, desenhar_cartao_central(escala, vezes_hoje),
                         lambda sw, sh, w, h: ((sw - w) // 2, (sh - h) // 2), duracao_ms)


class AlertaDiscreto(_Alerta):
    def __init__(self, root: tk.Misc, escala: float, duracao_ms: int, vezes_hoje: int | None):
        margem = int(20 * escala)
        super().__init__(root, desenhar_banner(escala, vezes_hoje),
                         lambda sw, sh, w, h: (sw - w - margem, margem), duracao_ms)
