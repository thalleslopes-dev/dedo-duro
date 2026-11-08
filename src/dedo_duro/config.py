"""Configuração do app e caminhos no disco.

- Código e recursos fixos (logo, ícone): dentro do pacote.
- Dados do usuário, modelos baixados, sons e logs: %LOCALAPPDATA%\\DedoDuro
  (fora da pasta do código, então um `git add .` nunca publica seus dados).
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

RECURSOS_PACOTE = Path(__file__).parent / "recursos"


@dataclass(frozen=True)
class Caminhos:
    raiz: Path

    @classmethod
    def padrao(cls) -> Caminhos:
        base = os.environ.get("DEDO_DURO_DADOS") or Path(os.environ.get("LOCALAPPDATA", Path.home())) / "DedoDuro"
        return cls(Path(base))

    @property
    def historico(self) -> Path:
        return self.raiz / "historico.csv"

    @property
    def recorde(self) -> Path:
        return self.raiz / "recorde.json"

    @property
    def preferencias(self) -> Path:
        return self.raiz / "preferencias.json"

    @property
    def exemplos(self) -> Path:
        return self.raiz / "treino" / "exemplos.csv"

    @property
    def modelo_pessoal(self) -> Path:
        return self.raiz / "treino" / "modelo.joblib"

    @property
    def modelos(self) -> Path:
        return self.raiz / "modelos"

    @property
    def sons(self) -> Path:
        return self.raiz / "sons"

    @property
    def logs(self) -> Path:
        return self.raiz / "logs"

    def criar_pastas(self) -> None:
        for pasta in (self.raiz, self.modelos, self.sons, self.logs, self.exemplos.parent):
            pasta.mkdir(parents=True, exist_ok=True)


@dataclass
class Config:
    """Parâmetros de comportamento. Os valores padrão são os recomendados."""

    fps: float = 3.0                  # quadros analisados por segundo
    limite: float = 0.25              # distância dedo-boca (em larguras de rosto) para a regra disparar
    confianca: float = 0.6            # probabilidade mínima do modelo pessoal
    seguidos: int = 2                 # quadros seguidos com mão na boca antes de alertar
    espera: float = 8.0               # segundos mínimos entre alertas
    duracao: float = 5.0              # segundos que o alerta de tela cheia fica visível
    duracao_discreto: float = 4.0     # segundos que o banner discreto fica visível
    repeticao: float = 120.0          # repetiu dentro dessa janela (s) -> alerta de tela cheia
    sempre_tela_cheia: bool = False
    pausar_em_chamada: bool = True
    checar_chamada_s: float = 3.0     # intervalo para checar se há reunião em andamento
    camera: int = 0
    preview: bool = False
    usar_modelo_pessoal: bool = True
    testar_alerta: bool = False
