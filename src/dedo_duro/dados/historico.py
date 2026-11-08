"""Histórico de alertas (CSV) e recorde do dia (JSON)."""
from __future__ import annotations

import csv
import datetime as dt
import json
import logging
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)
SEM_REGISTRO = "Sem registro"


@dataclass(frozen=True)
class Evento:
    quando: dt.datetime
    app: str
    tipo: str


class Historico:
    """Linhas: data, hora, app em foco, tipo. Aceita linhas antigas com só data e hora."""

    def __init__(self, arquivo: Path, arquivo_recorde: Path):
        self.arquivo = arquivo
        self.arquivo_recorde = arquivo_recorde

    def registrar(self, app: str, tipo: str, quando: dt.datetime | None = None) -> None:
        quando = quando or dt.datetime.now()
        self.arquivo.parent.mkdir(parents=True, exist_ok=True)
        with open(self.arquivo, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([quando.date().isoformat(), quando.strftime("%H:%M:%S"), app, tipo])

    def eventos(self) -> list[Evento]:
        if not self.arquivo.exists():
            return []
        eventos = []
        with open(self.arquivo, encoding="utf-8") as f:
            for linha in csv.reader(f):
                try:
                    quando = dt.datetime.fromisoformat(f"{linha[0]}T{linha[1]}")
                except (IndexError, ValueError):
                    continue  # linha corrompida: ignora sem derrubar o app
                app = linha[2] if len(linha) > 2 and linha[2] else SEM_REGISTRO
                tipo = linha[3] if len(linha) > 3 else ""
                eventos.append(Evento(quando, app, tipo))
        return eventos

    def contar(self, dia: dt.date) -> int:
        return sum(1 for e in self.eventos() if e.quando.date() == dia)

    # ---- recorde do dia
    def ler_recorde(self, dia: dt.date) -> float:
        try:
            dados = json.loads(self.arquivo_recorde.read_text(encoding="utf-8"))
            return float(dados["segundos"]) if dados.get("data") == dia.isoformat() else 0.0
        except FileNotFoundError:
            return 0.0
        except (OSError, ValueError, KeyError):
            log.warning("Arquivo de recorde inválido; começando do zero")
            return 0.0

    def salvar_recorde(self, dia: dt.date, segundos: float) -> None:
        self.arquivo_recorde.parent.mkdir(parents=True, exist_ok=True)
        self.arquivo_recorde.write_text(json.dumps({"data": dia.isoformat(), "segundos": int(segundos)}),
                                        encoding="utf-8")
