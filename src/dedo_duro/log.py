"""Logs em arquivo (rotativo). Rodando sem console (pythonw), é o único jeito de ver o que deu errado."""
from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

FORMATO = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"


def configurar(pasta_logs: Path, nivel: int = logging.INFO) -> Path:
    pasta_logs.mkdir(parents=True, exist_ok=True)
    arquivo = pasta_logs / "dedo-duro.log"
    handlers: list[logging.Handler] = [
        RotatingFileHandler(arquivo, maxBytes=1_000_000, backupCount=3, encoding="utf-8"),
    ]
    if sys.stderr is not None:  # com pythonw não existe console
        handlers.append(logging.StreamHandler())
    logging.basicConfig(level=nivel, format=FORMATO, handlers=handlers, force=True)

    def registrar_excecao(tipo, valor, tb):
        logging.getLogger("dedo_duro").critical("Erro não tratado", exc_info=(tipo, valor, tb))

    sys.excepthook = registrar_excecao
    return arquivo
