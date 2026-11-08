"""Decide se é "mão na boca": regra de distância ou modelo pessoal treinado."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .geometria import MedidaMao

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Decisao:
    na_boca: bool
    valor: float  # distância (regra) ou probabilidade (modelo)


class Decisor(Protocol):
    descricao: str

    def decidir(self, mao: MedidaMao) -> Decisao: ...


class RegraDistancia:
    def __init__(self, limite: float):
        self.limite = limite
        self.descricao = f"regra (limite {limite})"

    def decidir(self, mao: MedidaMao) -> Decisao:
        return Decisao(mao.distancia <= self.limite, mao.distancia)


class ModeloPessoal:
    def __init__(self, modelo, confianca: float):
        self.modelo = modelo
        self.confianca = confianca
        self.descricao = "modelo pessoal"

    def decidir(self, mao: MedidaMao) -> Decisao:
        prob = float(self.modelo.predict_proba([mao.features])[0][1])
        return Decisao(prob >= self.confianca, prob)


def criar_decisor(arquivo_modelo: Path, usar_modelo: bool, limite: float, confianca: float) -> Decisor:
    if usar_modelo and arquivo_modelo.exists():
        import joblib

        try:
            return ModeloPessoal(joblib.load(arquivo_modelo), confianca)
        except Exception:
            log.exception("Modelo pessoal inválido; usando a regra de distância")
    return RegraDistancia(limite)
