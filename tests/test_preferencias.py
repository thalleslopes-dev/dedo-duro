from dedo_duro.dados.preferencias import Preferencias


def test_executar_ao_ligar_vem_marcado_por_padrao(tmp_path):
    assert Preferencias(tmp_path / "preferencias.json").executar_ao_ligar is True


def test_desmarcar_persiste(tmp_path):
    arq = tmp_path / "preferencias.json"
    Preferencias(arq).executar_ao_ligar = False
    assert Preferencias(arq).executar_ao_ligar is False


def test_arquivo_corrompido_usa_padrao(tmp_path):
    arq = tmp_path / "preferencias.json"
    arq.write_text("{quebrado", encoding="utf-8")
    assert Preferencias(arq).executar_ao_ligar is True
