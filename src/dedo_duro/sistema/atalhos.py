"""Atalhos do Windows: iniciar com o sistema e atalho para abrir o app."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_INICIAR = Path(os.environ.get("APPDATA", "")) / "Microsoft/Windows/Start Menu/Programs/Startup"
ATALHO_INICIO = _INICIAR / "Dedo-Duro.lnk"
_ATALHOS_ANTIGOS = [_INICIAR / "Sem roer unha.lnk"]
_SEM_JANELA = 0x08000000  # CREATE_NO_WINDOW


def alvo_do_app() -> tuple[Path, str]:
    """(executável, argumentos) para abrir o app sem console."""
    if getattr(sys, "frozen", False):  # app instalado (empacotado com PyInstaller)
        return Path(sys.executable), ""
    exe = Path(sys.prefix) / "Scripts" / "dedo-duro.exe"  # criado pelo `pip install` (gui-scripts)
    if exe.exists():
        return exe, ""
    return Path(sys.executable).with_name("pythonw.exe"), "-m dedo_duro"


def _ps(texto: object) -> str:
    """Literal de string do PowerShell (aspas simples; apóstrofo vira '')."""
    return "'" + str(texto).replace("'", "''") + "'"


def criar_atalho(destino: Path, icone: Path) -> None:
    alvo, args = alvo_do_app()
    script = (f"$s=(New-Object -ComObject WScript.Shell).CreateShortcut({_ps(destino)});"
              f"$s.TargetPath={_ps(alvo)};$s.Arguments={_ps(args)};"
              f"$s.WorkingDirectory={_ps(Path.home())};$s.IconLocation={_ps(icone)};$s.Save()")
    subprocess.run(["powershell", "-NoProfile", "-Command", script], check=True, creationflags=_SEM_JANELA)


def executa_ao_ligar() -> bool:
    return ATALHO_INICIO.exists()


def definir_executar_ao_ligar(ligar: bool, icone: Path) -> None:
    """Cria (ou regrava, apontando para a instalação atual) ou remove o atalho na pasta Inicializar.
    O app aberto por esse atalho começa minimizado: só o processo, o mascote na barra e na bandeja."""
    for antigo in _ATALHOS_ANTIGOS:
        antigo.unlink(missing_ok=True)
    if ligar:
        criar_atalho(ATALHO_INICIO, icone)
    else:
        ATALHO_INICIO.unlink(missing_ok=True)
