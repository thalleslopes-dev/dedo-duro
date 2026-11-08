import numpy as np
import pytest

from dedo_duro.deteccao.geometria import N_FEATURES, PONTAS_DOS_DEDOS, mao_mais_proxima, medir_mao


def _mao(perto_de: np.ndarray, distancia_px: float) -> np.ndarray:
    """Mão longe da boca, com a ponta do indicador a `distancia_px` dela."""
    pontos = np.full((21, 2), 1000.0)
    pontos[8] = perto_de + [distancia_px, 0]
    return pontos


def test_distancia_normalizada_pela_largura_do_rosto():
    boca = np.array([100.0, 100.0])
    medida = medir_mao(_mao(boca, 50), boca, largura_rosto=200)
    assert medida.distancia == pytest.approx(0.25)
    assert medida.features.shape == (N_FEATURES,)


def test_medida_nao_depende_da_distancia_ate_a_camera():
    boca = np.array([100.0, 100.0])
    perto = medir_mao(_mao(boca, 50), boca, largura_rosto=200)
    longe = medir_mao(_mao(boca, 25), boca, largura_rosto=100)  # tudo pela metade
    assert perto.distancia == pytest.approx(longe.distancia)


def test_usa_a_ponta_de_dedo_mais_proxima():
    boca = np.zeros(2)
    pontos = np.full((21, 2), 500.0)
    pontos[PONTAS_DOS_DEDOS[0]] = [30, 40]  # polegar a 50 px
    pontos[0] = [1, 1]                     # pulso perto, mas não é ponta de dedo
    assert medir_mao(pontos, boca, 100).distancia == pytest.approx(0.5)


def test_escolhe_a_mao_mais_proxima():
    boca = np.zeros(2)
    longe, perto = _mao(boca, 300), _mao(boca, 20)
    assert mao_mais_proxima([longe, perto], boca, 100).distancia == pytest.approx(0.2)
    assert mao_mais_proxima([], boca, 100) is None


def test_largura_invalida():
    with pytest.raises(ValueError):
        medir_mao(np.zeros((21, 2)), np.zeros(2), 0)
