from dedo_duro.config import Config
from dedo_duro.monitor import MAX_SALTO_S, Monitor, TipoAlerta


def _monitor(**kw):
    return Monitor(Config(seguidos=2, espera=8, repeticao=120, **kw))


def test_precisa_de_quadros_seguidos():
    m = _monitor()
    assert m.registrar_quadro(True, 0.0) is None
    assert m.registrar_quadro(True, 0.3) is TipoAlerta.DISCRETO


def test_quadro_sem_mao_zera_a_sequencia():
    m = _monitor()
    m.registrar_quadro(True, 0.0)
    m.registrar_quadro(False, 0.3)
    assert m.registrar_quadro(True, 0.6) is None


def test_respeita_espera_entre_alertas():
    m = _monitor()
    m.registrar_quadro(True, 0.0)
    assert m.registrar_quadro(True, 0.3) is TipoAlerta.DISCRETO
    assert m.registrar_quadro(True, 5.0) is None  # ainda dentro dos 8 s


def test_repetir_dentro_da_janela_vira_tela_cheia():
    m = _monitor()
    m.registrar_quadro(True, 0.0)
    m.registrar_quadro(True, 0.3)
    assert m.registrar_quadro(True, 30.0) is TipoAlerta.TELA_CHEIA


def test_depois_da_janela_volta_a_ser_discreto():
    m = _monitor()
    m.registrar_quadro(True, 0.0)
    m.registrar_quadro(True, 0.3)
    m.registrar_quadro(False, 1.0)
    m.registrar_quadro(True, 500.0)
    assert m.registrar_quadro(True, 500.3) is TipoAlerta.DISCRETO


def test_sempre_tela_cheia():
    m = _monitor(sempre_tela_cheia=True)
    m.registrar_quadro(True, 0.0)
    assert m.registrar_quadro(True, 0.3) is TipoAlerta.TELA_CHEIA


def test_tempo_sem_alerta_e_recorde():
    m = _monitor()
    m.contar_tempo(3.0, vigiando=True)
    m.contar_tempo(3.0, vigiando=False)  # pausado não conta
    assert m.sem_alerta_s == 3.0
    m.registrar_quadro(True, 0.0)
    m.registrar_quadro(True, 0.3)  # alerta zera o contador, mas o recorde fica
    assert m.sem_alerta_s == 0.0
    assert m.recorde_s == 3.0


def test_ignora_saltos_grandes_de_tempo():
    m = _monitor()
    m.contar_tempo(3600.0, vigiando=True)  # ex.: notebook suspenso
    assert m.sem_alerta_s == MAX_SALTO_S


def test_novo_dia_zera_recorde():
    m = Monitor(Config(), recorde_s=100.0)
    m.novo_dia()
    assert m.recorde_s == 0.0
