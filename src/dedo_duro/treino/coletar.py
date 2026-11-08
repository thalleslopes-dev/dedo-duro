"""Grava exemplos para o modelo pessoal. Salva só os 42 números da mão, nunca imagens."""
from __future__ import annotations

import csv
import time

import cv2

from ..config import Caminhos
from ..deteccao.camera import Camera
from ..deteccao.detector import Detector, desenhar
from ..deteccao.modelos import garantir_arquivos

ROTULOS = {"normal": 0, "roendo": 1}
CONTAGEM_REGRESSIVA_S = 3


def coletar(caminhos: Caminhos, rotulo: str, segundos: int = 60, fps: float = 5, indice_camera: int = 0) -> int:
    arquivos = garantir_arquivos(caminhos.modelos)
    detector = Detector(arquivos["hand_landmarker.task"], arquivos["blaze_face_short_range.tflite"])
    camera = Camera(indice_camera)
    if not camera.abrir():
        raise SystemExit("Não consegui abrir a câmera (está em uso por outro app?).")

    caminhos.exemplos.parent.mkdir(parents=True, exist_ok=True)
    inicio = time.monotonic() + CONTAGEM_REGRESSIVA_S
    salvos = 0
    try:
        with open(caminhos.exemplos, "a", newline="", encoding="utf-8") as f:
            escritor = csv.writer(f)
            while True:
                t0 = time.monotonic()
                frame = camera.ler()
                if frame is None and not camera.abrir():
                    break
                if frame is None:
                    continue
                analise = detector.analisar(frame)
                restante = inicio + segundos - t0
                if restante <= 0:
                    break
                if t0 < inicio:
                    texto = f"Comecando em {inicio - t0:.0f}s... ({rotulo})"
                else:
                    if analise and analise.mao:
                        escritor.writerow([ROTULOS[rotulo], *analise.mao.features.round(4)])
                        salvos += 1
                    texto = f"{rotulo}: {salvos} exemplos | {restante:.0f}s"
                cv2.imshow("coleta (q para parar)", desenhar(frame, analise, texto))
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
                time.sleep(max(0.0, 1 / fps - (time.monotonic() - t0)))
    finally:
        camera.soltar()
        cv2.destroyAllWindows()
    return salvos
