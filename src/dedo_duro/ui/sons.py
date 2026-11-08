"""Sons dos alertas: 'dings' de sino gerados em .wav (substituíveis por qualquer .wav do usuário)."""
from __future__ import annotations

import wave
import winsound
from pathlib import Path

import numpy as np

TAXA = 44100
_MI6, _SI6 = 1318.51, 1975.53
RECEITAS = {
    "forte": ([(0.00, _MI6), (0.16, _SI6), (0.75, _MI6), (0.91, _SI6)], 0.85),  # dois dings, repetidos
    "suave": ([(0.00, _MI6), (0.16, _SI6)], 0.45),                              # um ding, mais baixo
}


def _sino(freq: float, duracao: float = 1.1) -> np.ndarray:
    t = np.arange(int(duracao * TAXA)) / TAXA
    parciais = [(1.0, 1.0, 0.55), (2.0, 0.45, 0.30), (2.76, 0.25, 0.18), (5.4, 0.08, 0.08)]  # (mult, amp, decaimento)
    som = sum(a * np.sin(2 * np.pi * freq * m * t) * np.exp(-t / tau) for m, a, tau in parciais)
    return som * (1 - np.exp(-t / 0.003))  # ataque rápido, sem estalo


def gerar_som(destino: Path, eventos: list[tuple[float, float]], volume: float) -> None:
    sinal = np.zeros(int((eventos[-1][0] + 1.2) * TAXA))
    for inicio, freq in eventos:
        s = _sino(freq)
        i = int(inicio * TAXA)
        sinal[i:i + len(s)] += s[: len(sinal) - i]
    amostras = (sinal / np.max(np.abs(sinal)) * volume * 32767).astype(np.int16)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(destino), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(TAXA)
        w.writeframes(amostras.tobytes())


class Sons:
    def __init__(self, pasta: Path):
        self.pasta = pasta

    def arquivo(self, tipo: str) -> Path:
        arq = self.pasta / f"alerta_{tipo}.wav"
        if not arq.exists():
            gerar_som(arq, *RECEITAS[tipo])
        return arq

    def tocar(self, forte: bool) -> None:
        winsound.PlaySound(str(self.arquivo("forte" if forte else "suave")), winsound.SND_FILENAME | winsound.SND_ASYNC)
