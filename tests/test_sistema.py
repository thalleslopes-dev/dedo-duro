from dedo_duro.sistema.atalhos import _ps
from dedo_duro.sistema.chamadas import nome_da_chave
from dedo_duro.sistema.janelas import DESCONHECIDO, RastreadorDeFoco, nome_amigavel


def test_nome_amigavel():
    assert nome_amigavel(r"C:\Program Files\Microsoft VS Code\Code.exe") == "VS Code"
    assert nome_amigavel(r"C:\apps\algumacoisa.exe") == "Algumacoisa"


def test_nome_da_chave_do_registro():
    assert nome_da_chave("C:#Users#x#AppData#Local#slack#app-4.52.171#slack.exe") == "Slack"
    assert nome_da_chave("5319275A.WhatsAppDesktop_cv1g1gvanyjgm") == "WhatsAppDesktop"


def test_rastreador_ignora_as_janelas_do_proprio_app():
    respostas = iter(["Slack", "Python", "Pythonw", "Chrome"])
    foco = RastreadorDeFoco(consultar=lambda: next(respostas))
    assert foco.ultimo == DESCONHECIDO
    assert foco.atualizar() == "Slack"
    assert foco.atualizar() == "Slack"
    assert foco.atualizar() == "Slack"
    assert foco.atualizar() == "Chrome"


def test_literal_powershell_escapa_apostrofo():
    assert _ps(r"C:\Users\D'Ávila\app") == r"'C:\Users\D''Ávila\app'"
