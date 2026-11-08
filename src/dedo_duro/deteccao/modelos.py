"""Arquivos baixados na primeira execução (modelos do MediaPipe e fonte de ícones)."""
from __future__ import annotations

import logging
import shutil
import urllib.request
from pathlib import Path

log = logging.getLogger(__name__)

_BASE_MP = "https://storage.googleapis.com/mediapipe-models"
ARQUIVOS = {
    "hand_landmarker.task": f"{_BASE_MP}/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task",
    "blaze_face_short_range.tflite":
        f"{_BASE_MP}/face_detector/blaze_face_short_range/float16/latest/blaze_face_short_range.tflite",
    "tabler-icons.ttf": "https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3.31.0/dist/fonts/tabler-icons.ttf",
}


def garantir_arquivos(pasta: Path) -> dict[str, Path]:
    """Baixa o que estiver faltando e devolve {nome: caminho}. A internet só é usada aqui, uma vez."""
    pasta.mkdir(parents=True, exist_ok=True)
    caminhos = {}
    for nome, url in ARQUIVOS.items():
        destino = pasta / nome
        if not destino.exists():
            log.info("Baixando %s", nome)
            temporario = destino.with_suffix(destino.suffix + ".parcial")
            with urllib.request.urlopen(url, timeout=60) as resposta, open(temporario, "wb") as f:
                shutil.copyfileobj(resposta, f)
            temporario.replace(destino)  # só aparece com o nome final se o download terminou
        caminhos[nome] = destino
    return caminhos
