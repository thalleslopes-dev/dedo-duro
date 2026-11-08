"""Preferências do usuário que sobrevivem entre execuções (JSON)."""
from __future__ import annotations

import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)

PADROES = {
    "executar_ao_ligar": True,  # marcado por padrão: o app abre sozinho quando o computador liga
}


class Preferencias:
    def __init__(self, arquivo: Path):
        self.arquivo = arquivo
        self._dados = dict(PADROES)
        try:
            self._dados.update(json.loads(arquivo.read_text(encoding="utf-8")))
        except FileNotFoundError:
            pass
        except (OSError, ValueError):
            log.warning("Preferências inválidas; usando os padrões")

    @property
    def executar_ao_ligar(self) -> bool:
        return bool(self._dados["executar_ao_ligar"])

    @executar_ao_ligar.setter
    def executar_ao_ligar(self, valor: bool) -> None:
        self._dados["executar_ao_ligar"] = bool(valor)
        self.salvar()

    def salvar(self) -> None:
        self.arquivo.parent.mkdir(parents=True, exist_ok=True)
        self.arquivo.write_text(json.dumps(self._dados, indent=2), encoding="utf-8")
