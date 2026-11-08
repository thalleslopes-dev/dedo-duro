"""Detector MediaPipe: transforma um quadro em medidas. Nenhuma imagem é salva."""
from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import BaseOptions, vision

from .geometria import MedidaMao, mao_mais_proxima

BOCA = 3                 # índice do ponto "boca" no detector de rosto (BlazeFace)
MEMORIA_ROSTO_S = 3.0    # a mão na boca às vezes esconde o rosto: usa a última posição conhecida


@dataclass(frozen=True)
class Analise:
    boca: np.ndarray                 # posição da boca em pixels
    mao: MedidaMao | None            # None = rosto visível, mas nenhuma mão


class Detector:
    def __init__(self, modelo_mao: Path, modelo_rosto: Path, relogio=time.monotonic):
        self._relogio = relogio
        self._maos = vision.HandLandmarker.create_from_options(vision.HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(modelo_mao)),
            running_mode=vision.RunningMode.IMAGE,
            num_hands=2,
        ))
        self._rosto = vision.FaceDetector.create_from_options(vision.FaceDetectorOptions(
            base_options=BaseOptions(model_asset_path=str(modelo_rosto)),
            running_mode=vision.RunningMode.IMAGE,
        ))
        self._ultimo_rosto: tuple[np.ndarray, float, float] | None = None  # (boca, largura, instante)

    def analisar(self, frame_bgr: np.ndarray) -> Analise | None:
        """None quando não há rosto (nem lembrança recente dele)."""
        h, w = frame_bgr.shape[:2]
        imagem = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
        agora = self._relogio()

        rostos = self._rosto.detect(imagem).detections
        if rostos:
            r = max(rostos, key=lambda d: d.bounding_box.width)
            kp = r.keypoints[BOCA]
            self._ultimo_rosto = (np.array([kp.x * w, kp.y * h]), float(r.bounding_box.width), agora)
        if self._ultimo_rosto is None or agora - self._ultimo_rosto[2] > MEMORIA_ROSTO_S:
            return None
        boca, largura, _ = self._ultimo_rosto

        maos = [np.array([[p.x * w, p.y * h] for p in mao]) for mao in self._maos.detect(imagem).hand_landmarks]
        return Analise(boca=boca, mao=mao_mais_proxima(maos, boca, largura))


def desenhar(frame: np.ndarray, analise: Analise | None, texto: str = "", alerta: bool = False) -> np.ndarray:
    """Desenha boca e pontos da mão (só para as janelas de preview/coleta)."""
    if analise:
        cv2.circle(frame, tuple(analise.boca.astype(int)), 8, (0, 0, 255), -1)
        if analise.mao:
            for x, y in analise.mao.pontos.astype(int):
                cv2.circle(frame, (x, y), 3, (255, 200, 0), -1)
    if texto:
        cv2.putText(frame, texto, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255) if alerta else (0, 200, 0), 2)
    return frame
