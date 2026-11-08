from dedo_duro.cli import config_dos_args, criar_parser
from dedo_duro.config import Config


def test_padroes_batem_com_a_config():
    assert config_dos_args(criar_parser().parse_args([])) == Config()


def test_flags_negativas_e_valores():
    args = criar_parser().parse_args(["--sem-modelo", "--sem-pausa-reuniao", "--limite", "0.4", "--preview"])
    cfg = config_dos_args(args)
    assert cfg.usar_modelo_pessoal is False
    assert cfg.pausar_em_chamada is False
    assert cfg.limite == 0.4 and cfg.preview is True


def test_subcomandos():
    p = criar_parser()
    assert p.parse_args(["coletar", "roendo"]).rotulo == "roendo"
    assert p.parse_args(["treinar"]).comando == "treinar"
