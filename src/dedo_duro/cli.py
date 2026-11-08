"""Linha de comando.

    dedo-duro                      abre o app (bandeja + barra de tarefas)
    dedo-duro --preview            abre mostrando a câmera com os pontos (para calibrar)
    dedo-duro coletar roendo       grava exemplos para o modelo pessoal
    dedo-duro treinar              treina o modelo pessoal
"""
from __future__ import annotations

import argparse
import ctypes
import logging
import sys
from dataclasses import fields

from . import NOME, __version__, log
from .config import Caminhos, Config

_MUTEX = "DedoDuro_instancia_unica"
_ERROR_ALREADY_EXISTS = 183


def _opcoes_do_app(p: argparse.ArgumentParser) -> None:
    padrao = Config()
    p.add_argument("--fps", type=float, default=padrao.fps, help="quadros analisados por segundo (padrão %(default)s)")
    p.add_argument("--limite", type=float, default=padrao.limite,
                   help="distância dedo-boca, em larguras de rosto, que dispara a regra (padrão %(default)s)")
    p.add_argument("--confianca", type=float, default=padrao.confianca, help="probabilidade mínima do modelo pessoal")
    p.add_argument("--seguidos", type=int, default=padrao.seguidos, help="quadros seguidos antes de alertar")
    p.add_argument("--espera", type=float, default=padrao.espera, help="segundos mínimos entre alertas")
    p.add_argument("--duracao", type=float, default=padrao.duracao, help="segundos do alerta de tela cheia")
    p.add_argument("--repeticao", type=float, default=padrao.repeticao,
                   help="repetiu dentro desses segundos -> alerta de tela cheia")
    p.add_argument("--sempre-tela-cheia", action="store_true", help="desliga o alerta discreto")
    p.add_argument("--sem-pausa-reuniao", dest="pausar_em_chamada", action="store_false",
                   help="não pausa durante chamadas")
    p.add_argument("--camera", type=int, default=padrao.camera, help="índice da webcam")
    p.add_argument("--preview", action="store_true", help="mostra a câmera com os pontos")
    p.add_argument("--sem-modelo", dest="usar_modelo_pessoal", action="store_false",
                   help="ignora o modelo pessoal e usa a regra de distância")
    p.add_argument("--testar-alerta", action="store_true", help="dispara um alerta ao abrir")


def criar_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="dedo-duro", description=f"{NOME}: te dedura quando o dedo vai pra boca.")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    _opcoes_do_app(p)
    sub = p.add_subparsers(dest="comando")
    c = sub.add_parser("coletar", help="grava exemplos (só números) para o modelo pessoal")
    c.add_argument("rotulo", choices=["roendo", "normal"])
    c.add_argument("--segundos", type=int, default=60)
    sub.add_parser("treinar", help="treina o modelo pessoal com os exemplos coletados")
    return p


def config_dos_args(args: argparse.Namespace) -> Config:
    nomes = {f.name for f in fields(Config)}
    return Config(**{k: v for k, v in vars(args).items() if k in nomes})


def _ja_esta_rodando() -> bool:
    ctypes.windll.kernel32.CreateMutexW(None, False, _MUTEX)
    return ctypes.windll.kernel32.GetLastError() == _ERROR_ALREADY_EXISTS


def main(argv: list[str] | None = None) -> None:
    args = criar_parser().parse_args(argv)
    caminhos = Caminhos.padrao()
    caminhos.criar_pastas()
    arquivo_log = log.configurar(caminhos.logs)
    logger = logging.getLogger("dedo_duro")

    if args.comando == "coletar":
        from .treino.coletar import coletar

        n = coletar(caminhos, args.rotulo, args.segundos, indice_camera=args.camera)
        print(f"{n} exemplos '{args.rotulo}' salvos em {caminhos.exemplos}")
        return
    if args.comando == "treinar":
        from .treino.treinar import treinar

        r = treinar(caminhos)
        print(f"Exemplos: {r.n_roendo} roendo, {r.n_normal} normal")
        print(f"Acurácia estimada: {r.acuracia:.1%}. Modelo salvo; o app passa a usá-lo ao reabrir.")
        return

    if _ja_esta_rodando():
        ctypes.windll.user32.MessageBoxW(None, "O app já está rodando (veja o mascote perto do relógio).", NOME, 0x40)
        sys.exit(0)
    logger.info("%s %s · dados em %s · log em %s", NOME, __version__, caminhos.raiz, arquivo_log)
    from .app import DedoDuro

    DedoDuro(config_dos_args(args), caminhos).rodar()
