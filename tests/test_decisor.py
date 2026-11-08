import numpy as np

from dedo_duro.deteccao.decisor import ModeloPessoal, RegraDistancia, criar_decisor
from dedo_duro.deteccao.geometria import MedidaMao


def _medida(distancia: float) -> MedidaMao:
    return MedidaMao(distancia=distancia, features=np.zeros(42), pontos=np.zeros((21, 2)))


def test_regra_de_distancia():
    regra = RegraDistancia(limite=0.25)
    assert regra.decidir(_medida(0.2)).na_boca
    assert not regra.decidir(_medida(0.3)).na_boca


def test_modelo_pessoal_usa_a_probabilidade():
    class Falso:
        def predict_proba(self, X):
            return np.array([[0.3, 0.7]])

    d = ModeloPessoal(Falso(), confianca=0.6).decidir(_medida(9.0))
    assert d.na_boca and d.valor == 0.7


def test_sem_modelo_usa_a_regra(tmp_path):
    assert isinstance(criar_decisor(tmp_path / "nao_existe.joblib", True, 0.25, 0.6), RegraDistancia)


def test_modelo_corrompido_cai_para_a_regra(tmp_path):
    arq = tmp_path / "modelo.joblib"
    arq.write_bytes(b"lixo")
    assert isinstance(criar_decisor(arq, True, 0.25, 0.6), RegraDistancia)
