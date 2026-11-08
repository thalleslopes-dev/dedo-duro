"""Nome do app em foco (só o nome do programa; nunca o título da janela)."""
from __future__ import annotations

import ctypes
import os
from ctypes import wintypes

DESCONHECIDO = "Desconhecido"
NOMES_AMIGAVEIS = {
    "code.exe": "VS Code", "cursor.exe": "Cursor", "chrome.exe": "Chrome", "msedge.exe": "Edge",
    "firefox.exe": "Firefox", "brave.exe": "Brave", "arc.exe": "Arc", "slack.exe": "Slack",
    "ms-teams.exe": "Teams", "teams.exe": "Teams", "zoom.exe": "Zoom", "whatsapp.exe": "WhatsApp",
    "whatsapp.root.exe": "WhatsApp", "excel.exe": "Excel", "winword.exe": "Word", "powerpnt.exe": "PowerPoint",
    "outlook.exe": "Outlook", "olk.exe": "Outlook", "explorer.exe": "Explorador", "notion.exe": "Notion",
    "windowsterminal.exe": "Terminal", "spotify.exe": "Spotify", "discord.exe": "Discord", "figma.exe": "Figma",
    "loom.exe": "Loom", "obsidian.exe": "Obsidian",
}
_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


def nome_amigavel(caminho_exe: str) -> str:
    exe = os.path.basename(caminho_exe)
    return NOMES_AMIGAVEIS.get(exe.lower(), exe.rsplit(".", 1)[0].capitalize())


def _api():
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
                                                    ctypes.POINTER(wintypes.DWORD)]
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    return user32, kernel32


def app_em_foco() -> str:
    user32, kernel32 = _api()
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return DESCONHECIDO
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    processo = kernel32.OpenProcess(_PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
    if not processo:
        return DESCONHECIDO
    try:
        buf = ctypes.create_unicode_buffer(512)
        tamanho = wintypes.DWORD(512)
        if not kernel32.QueryFullProcessImageNameW(processo, 0, buf, ctypes.byref(tamanho)):
            return DESCONHECIDO
        return nome_amigavel(buf.value)
    finally:
        kernel32.CloseHandle(processo)


class RastreadorDeFoco:
    """Guarda o último app em foco que não seja o próprio Dedo-Duro (alerta e resumo roubam o foco)."""

    def __init__(self, consultar=app_em_foco):
        self._consultar = consultar
        self.ultimo = DESCONHECIDO

    def atualizar(self) -> str:
        app = self._consultar()
        if not app.lower().startswith("python") and app != "Dedo-duro":
            self.ultimo = app
        return self.ultimo
