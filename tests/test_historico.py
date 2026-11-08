import datetime as dt

from dedo_duro.dados.historico import SEM_REGISTRO, Historico


def _hist(tmp_path):
    return Historico(tmp_path / "historico.csv", tmp_path / "recorde.json")


def test_registrar_e_ler(tmp_path):
    h = _hist(tmp_path)
    quando = dt.datetime(2026, 11, 8, 15, 30, 0)
    h.registrar("Slack", "discreto", quando)
    [e] = h.eventos()
    assert (e.quando, e.app, e.tipo) == (quando, "Slack", "discreto")


def test_aceita_linhas_antigas_e_ignora_corrompidas(tmp_path):
    h = _hist(tmp_path)
    h.arquivo.write_text("2026-11-08,10:00:00\nlixo\n2026-11-08,11:00:00,Chrome,tela_cheia\n", encoding="utf-8")
    eventos = h.eventos()
    assert [e.app for e in eventos] == [SEM_REGISTRO, "Chrome"]


def test_contar_por_dia(tmp_path):
    h = _hist(tmp_path)
    h.registrar("A", "discreto", dt.datetime(2026, 11, 7, 10))
    h.registrar("A", "discreto", dt.datetime(2026, 11, 8, 10))
    h.registrar("A", "discreto", dt.datetime(2026, 11, 8, 11))
    assert h.contar(dt.date(2026, 11, 8)) == 2


def test_recorde_vale_so_para_o_dia(tmp_path):
    h = _hist(tmp_path)
    assert h.ler_recorde(dt.date(2026, 11, 8)) == 0.0  # sem arquivo
    h.salvar_recorde(dt.date(2026, 11, 8), 754.9)
    assert h.ler_recorde(dt.date(2026, 11, 8)) == 754
    assert h.ler_recorde(dt.date(2026, 11, 9)) == 0.0


def test_recorde_corrompido_nao_quebra(tmp_path):
    h = _hist(tmp_path)
    h.arquivo_recorde.write_text("{nao é json", encoding="utf-8")
    assert h.ler_recorde(dt.date(2026, 11, 8)) == 0.0
