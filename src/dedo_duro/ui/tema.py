"""Identidade visual: cores (paleta Apple, modo claro), fontes, logo e ícones (Tabler Icons)."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageTk

from ..config import RECURSOS_PACOTE

LOGO_PNG = RECURSOS_PACOTE / "logo.png"
ICONE_ICO = RECURSOS_PACOTE / "icone.ico"
FONTE_TITULO = "C:/Windows/Fonts/seguisb.ttf"  # Segoe UI Semibold
FONTE_TEXTO = "C:/Windows/Fonts/segoeui.ttf"

COR = {
    "fundo": "#F5F5F7",
    "cartao": "#FFFFFF",
    "texto": "#1D1D1F",
    "secundario": "#6E6E73",
    "terciario": "#AEAEB2",
    "divisor": "#E5E5EA",
    "vermelho": "#FF3B30",
    "vermelho_suave": "#FFE5E3",
    "verde": "#34C759",
    "laranja": "#FF9500",
    "azul": "#0A84FF",
    "azul_suave": "#E5F0FF",
    "hover": "#E8E8ED",
}

# códigos em https://tabler.io/icons
GLIFOS = {
    "mao": "\uec2e",        # hand-stop
    "pausa": "\ued45",      # player-pause
    "play": "\ued46",       # player-play
    "sair": "\ueb0d",       # power
    "ideia": "\uea51",      # bulb
    "grafico": "\uea59",    # chart-bar
    "desceu": "\uea15",     # arrow-down-right
    "subiu": "\uea24",      # arrow-up-right
}

_fonte_icones: Path | None = None


def definir_fonte_icones(caminho: Path) -> None:
    global _fonte_icones
    _fonte_icones = caminho


def icone_pil(nome: str, tamanho: int, cor: str) -> Image.Image:
    if _fonte_icones is None:
        raise RuntimeError("Chame tema.definir_fonte_icones() antes de desenhar ícones")
    fonte = ImageFont.truetype(str(_fonte_icones), tamanho)
    img = Image.new("RGBA", (tamanho, tamanho), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((tamanho / 2, tamanho / 2), GLIFOS[nome], font=fonte, fill=cor, anchor="mm")
    return img


def icone(nome: str, tamanho: int, cor: str) -> ImageTk.PhotoImage:
    """Guarde a referência retornada; senão o Tk descarta a imagem."""
    return ImageTk.PhotoImage(icone_pil(nome, tamanho, cor))


def logo(tamanho: int) -> ImageTk.PhotoImage:
    return ImageTk.PhotoImage(Image.open(LOGO_PNG).resize((tamanho, tamanho), Image.LANCZOS))
