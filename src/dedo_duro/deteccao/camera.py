"""Acesso à webcam."""
from __future__ import annotations

import cv2
import numpy as np


class Camera:
    def __init__(self, indice: int = 0):
        self.indice = indice
        self._cap: cv2.VideoCapture | None = None

    @property
    def aberta(self) -> bool:
        return self._cap is not None

    def abrir(self) -> bool:
        if self._cap is None:
            cap = cv2.VideoCapture(self.indice, cv2.CAP_DSHOW)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self._cap = cap if cap.isOpened() else None
        return self._cap is not None

    def ler(self) -> np.ndarray | None:
        """Quadro mais recente (descarta os antigos do buffer). Solta a câmera se a leitura falhar."""
        if self._cap is None:
            return None
        for _ in range(2):
            self._cap.grab()
        ok, frame = self._cap.retrieve()
        if not ok:
            self.soltar()
            return None
        return frame

    def soltar(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None
