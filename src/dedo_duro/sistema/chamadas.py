"""Detecta chamada em andamento: outro app usando câmera ou microfone (registro do Windows)."""
from __future__ import annotations

import winreg

from .janelas import nome_amigavel

_CONSENT = r"Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore"
IGNORAR = ("python", "dedo-duro")


def nome_da_chave(chave: str) -> str:
    """'C:#Program Files#...#slack.exe' -> 'Slack'; '5319275A.WhatsAppDesktop_cv1g...' -> 'WhatsAppDesktop'."""
    if "#" in chave:
        return nome_amigavel(chave.split("#")[-1])
    return chave.split("_")[0].split(".")[-1]


def apps_usando(recurso: str) -> list[str]:
    """Apps (fora este) usando 'webcam' ou 'microphone' agora. LastUsedTimeStop == 0 significa em uso."""
    em_uso: set[str] = set()

    def visitar(caminho: str, nivel: int) -> None:
        try:
            chave = winreg.OpenKey(winreg.HKEY_CURRENT_USER, caminho)
        except OSError:
            return
        with chave:
            nome = caminho.rsplit("\\", 1)[-1]
            try:
                parou, _ = winreg.QueryValueEx(chave, "LastUsedTimeStop")
                if parou == 0 and not any(i in nome.lower() for i in IGNORAR):
                    em_uso.add(nome_da_chave(nome))
            except OSError:
                pass
            if nivel < 2:
                i = 0
                while True:
                    try:
                        sub = winreg.EnumKey(chave, i)
                    except OSError:
                        break
                    visitar(f"{caminho}\\{sub}", nivel + 1)
                    i += 1

    visitar(f"{_CONSENT}\\{recurso}", 0)
    return sorted(em_uso)


def em_chamada() -> str | None:
    """Nome do app em chamada (microfone em uso = provavelmente reunião), ou None."""
    apps = apps_usando("webcam") + apps_usando("microphone")
    return apps[0] if apps else None
