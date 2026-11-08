"""Treina o modelo pessoal (Random Forest) com os exemplos coletados."""
from __future__ import annotations

from dataclasses import dataclass

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score

from ..config import Caminhos
from ..deteccao.geometria import N_FEATURES

MIN_POR_CLASSE = 20


@dataclass(frozen=True)
class ResultadoTreino:
    n_roendo: int
    n_normal: int
    acuracia: float


def carregar_exemplos(caminhos: Caminhos) -> tuple[np.ndarray, np.ndarray]:
    if not caminhos.exemplos.exists():
        raise SystemExit("Sem exemplos. Rode antes: dedo-duro coletar roendo  e  dedo-duro coletar normal")
    dados = np.loadtxt(caminhos.exemplos, delimiter=",", ndmin=2)
    if dados.shape[1] != N_FEATURES + 1:
        raise SystemExit(f"Arquivo de exemplos inválido: esperava {N_FEATURES + 1} colunas, achei {dados.shape[1]}")
    return dados[:, 1:], dados[:, 0].astype(int)


def treinar(caminhos: Caminhos) -> ResultadoTreino:
    X, y = carregar_exemplos(caminhos)
    n_roendo, n_normal = int((y == 1).sum()), int((y == 0).sum())
    if min(n_roendo, n_normal) < MIN_POR_CLASSE:
        raise SystemExit(f"Poucos exemplos ({n_roendo} roendo, {n_normal} normal). Mínimo {MIN_POR_CLASSE} de cada.")

    modelo = RandomForestClassifier(n_estimators=100, max_depth=10, class_weight="balanced", random_state=0)
    # Quadros seguidos são quase iguais: embaralhar faria a validação "colar" e superestimar a acurácia.
    # Sem embaralhar, cada parte da validação testa um trecho contínuo (e diferente) de cada gravação.
    acuracia = cross_val_score(modelo, X, y, cv=StratifiedKFold(n_splits=5, shuffle=False)).mean()
    modelo.fit(X, y)
    caminhos.modelo_pessoal.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(modelo, caminhos.modelo_pessoal)
    return ResultadoTreino(n_roendo, n_normal, float(acuracia))
