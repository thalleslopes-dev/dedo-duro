"""Cálculos puros sobre os pontos detectados (sem MediaPipe, sem câmera: fácil de testar)."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

PONTAS_DOS_DEDOS = (4, 8, 12, 16, 20)  # polegar, indicador, médio, anelar, mínimo (índices do MediaPipe)
N_PONTOS_MAO = 21
N_FEATURES = N_PONTOS_MAO * 2


@dataclass(frozen=True)
class MedidaMao:
    distancia: float          # menor distância ponta-do-dedo -> boca, em larguras de rosto
    features: np.ndarray      # 42 números: os 21 pontos relativos à boca, normalizados
    pontos: np.ndarray        # 21x2 em pixels (só para desenhar o preview)


def medir_mao(pontos_px: np.ndarray, boca_px: np.ndarray, largura_rosto: float) -> MedidaMao:
    """Mede uma mão em relação à boca. Normalizar pela largura do rosto torna a medida
    independente da distância até a câmera."""
    if largura_rosto <= 0:
        raise ValueError("largura_rosto deve ser positiva")
    relativos = (pontos_px - boca_px) / largura_rosto
    distancia = float(np.min(np.linalg.norm(relativos[list(PONTAS_DOS_DEDOS)], axis=1)))
    return MedidaMao(distancia=distancia, features=relativos.flatten(), pontos=pontos_px)


def mao_mais_proxima(maos_px: list[np.ndarray], boca_px: np.ndarray, largura_rosto: float) -> MedidaMao | None:
    medidas = [medir_mao(m, boca_px, largura_rosto) for m in maos_px]
    return min(medidas, key=lambda m: m.distancia) if medidas else None
