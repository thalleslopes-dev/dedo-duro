"""Orquestração: liga câmera, detector, decisor, monitor, histórico e interface. Sem regra de negócio própria."""
from __future__ import annotations

import ctypes
import datetime as dt
import logging
import queue
import time
import tkinter as tk

import cv2

from .config import Caminhos, Config
from .dados.historico import Historico
from .dados.preferencias import Preferencias
from .dados.resumo import calcular_resumo
from .deteccao.camera import Camera
from .deteccao.decisor import criar_decisor
from .deteccao.detector import Detector, desenhar
from .deteccao.modelos import garantir_arquivos
from .monitor import Estado, Monitor, TipoAlerta
from .sistema.atalhos import definir_executar_ao_ligar
from .sistema.chamadas import em_chamada
from .sistema.janelas import RastreadorDeFoco
from .ui import tema
from .ui.alertas import AlertaDiscreto, AlertaTelaCheia
from .ui.bandeja import AcoesBandeja, Bandeja
from .ui.janela import Acoes, JanelaControle
from .ui.janela_resumo import JanelaResumo
from .ui.sons import Sons
from .ui.textos import status_curto

log = logging.getLogger(__name__)
SALVAR_RECORDE_S = 60
APP_USER_MODEL_ID = "DedoDuro.App"


def criar_root() -> tuple[tk.Tk, float]:
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)  # nitidez em telas com zoom
        # identidade própria na barra de tarefas (senão o Windows agrupa como "Python")
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
    except (AttributeError, OSError):
        log.warning("Não foi possível ajustar DPI/identidade na barra de tarefas")
    root = tk.Tk()
    root.iconbitmap(default=str(tema.ICONE_ICO))  # vale para todas as janelas do app
    root.report_callback_exception = lambda *exc: log.error("Erro na interface", exc_info=exc)
    return root, root.winfo_fpixels("1i") / 96


class DedoDuro:
    def __init__(self, cfg: Config, caminhos: Caminhos):
        self.cfg = cfg
        arquivos = garantir_arquivos(caminhos.modelos)
        tema.definir_fonte_icones(arquivos["tabler-icons.ttf"])

        self.detector = Detector(arquivos["hand_landmarker.task"], arquivos["blaze_face_short_range.tflite"])
        self.decisor = criar_decisor(caminhos.modelo_pessoal, cfg.usar_modelo_pessoal, cfg.limite, cfg.confianca)
        self.camera = Camera(cfg.camera)
        self.historico = Historico(caminhos.historico, caminhos.recorde)
        self.preferencias = Preferencias(caminhos.preferencias)
        self.sons = Sons(caminhos.sons)
        self.foco = RastreadorDeFoco()

        self.dia = dt.date.today()
        self.monitor = Monitor(cfg, recorde_s=self.historico.ler_recorde(self.dia))
        self.alertas_hoje = self.historico.contar(self.dia)
        self.pausado = False
        self.app_em_chamada: str | None = None
        self.camera_ocupada = False
        self.saindo = False
        self._alerta = None
        self._janela_resumo: JanelaResumo | None = None
        self._ultima_checagem = float("-inf")
        self._ultimo_passo = time.monotonic()
        self._ultimo_salvamento = time.monotonic()
        self.fila: queue.Queue = queue.Queue()  # tarefas vindas da bandeja (outra thread)

        self.root, self.escala = criar_root()
        self.janela = JanelaControle(self.root, self.escala, Acoes(
            resumo=self.abrir_resumo, pausar=self.alternar_pausa, sair=self.sair,
            executar_ao_ligar=self.definir_executar_ao_ligar,
        ), executar_ao_ligar=self.preferencias.executar_ao_ligar)
        self.bandeja = Bandeja(AcoesBandeja(
            resumo=self.abrir_resumo, pausar=self.alternar_pausa, testar_alerta=self.testar_alerta,
            alternar_executar_ao_ligar=lambda: self.definir_executar_ao_ligar(
                not self.preferencias.executar_ao_ligar),
            sair=self.sair, status=self.status, pausado=lambda: self.pausado,
            executar_ao_ligar=lambda: self.preferencias.executar_ao_ligar,
        ), self.fila)
        self._sincronizar_atalho_de_inicio()
        log.info("Iniciado com %s, %.1f quadros/s", self.decisor.descricao, cfg.fps)

    # ---------- estado ----------
    @property
    def estado(self) -> Estado:
        if self.pausado:
            return Estado.PAUSADO
        if self.app_em_chamada:
            return Estado.EM_CHAMADA
        if self.camera_ocupada:
            return Estado.CAMERA_OCUPADA
        return Estado.VIGIANDO

    def status(self) -> str:
        return status_curto(self.estado, self.alertas_hoje, self.app_em_chamada)

    def _atualizar_interface(self) -> None:
        self.bandeja.atualizar(self.estado, self.status())
        self.janela.atualizar(self.estado, self.alertas_hoje, self.monitor.sem_alerta_s, self.app_em_chamada)

    # ---------- ações ----------
    def alternar_pausa(self) -> None:
        self.pausado = not self.pausado
        if self.pausado:
            self._soltar_camera()
        log.info("Pausado" if self.pausado else "Retomado")
        self._atualizar_interface()

    def definir_executar_ao_ligar(self, ligar: bool) -> None:
        self.preferencias.executar_ao_ligar = ligar
        self._sincronizar_atalho_de_inicio()
        self.janela.definir_executar_ao_ligar(ligar)
        log.info("Executar quando o computador ligar: %s", "sim" if ligar else "não")

    def _sincronizar_atalho_de_inicio(self) -> None:
        """A preferência manda: cria/regrava o atalho de inicialização ou remove. Marcado por padrão."""
        try:
            definir_executar_ao_ligar(self.preferencias.executar_ao_ligar, tema.ICONE_ICO)
        except Exception:
            log.exception("Não foi possível ajustar a inicialização com o Windows")

    def abrir_resumo(self) -> None:
        if self._janela_resumo and self._janela_resumo.top.winfo_exists():
            self._janela_resumo.top.destroy()
        resumo = calcular_resumo(self.historico.eventos(), dt.datetime.now())
        self._janela_resumo = JanelaResumo(self.root, self.escala, resumo, self.monitor.recorde_s, self.dia)

    def testar_alerta(self) -> None:
        self._mostrar_alerta(TipoAlerta.TELA_CHEIA, self.alertas_hoje or 1)

    def sair(self) -> None:
        self.saindo = True
        self.historico.salvar_recorde(self.dia, self.monitor.recorde_s)
        self._soltar_camera()
        self.bandeja.parar()
        self.root.destroy()
        log.info("Encerrado")

    # ---------- alerta ----------
    def _mostrar_alerta(self, tipo: TipoAlerta, vezes: int) -> None:
        forte = tipo is TipoAlerta.TELA_CHEIA
        self.sons.tocar(forte)
        if self._alerta and not self._alerta.fechando:
            self._alerta.fechar()
        if forte:
            self._alerta = AlertaTelaCheia(self.root, self.escala, int(self.cfg.duracao * 1000), vezes)
        else:
            self._alerta = AlertaDiscreto(self.root, self.escala, int(self.cfg.duracao_discreto * 1000), vezes)

    def _alertar(self, tipo: TipoAlerta) -> None:
        self.historico.registrar(self.foco.ultimo, tipo.value)
        self.alertas_hoje = self.historico.contar(self.dia)
        self._mostrar_alerta(tipo, self.alertas_hoje)

    # ---------- loop ----------
    def _soltar_camera(self) -> None:
        self.camera.soltar()
        cv2.destroyAllWindows()

    def _virada_do_dia(self) -> None:
        hoje = dt.date.today()
        if hoje != self.dia:
            self.historico.salvar_recorde(self.dia, self.monitor.recorde_s)
            self.dia = hoje
            self.monitor.novo_dia()
            self.alertas_hoje = self.historico.contar(hoje)

    def _checar_chamada(self, agora: float) -> None:
        if not self.cfg.pausar_em_chamada or agora - self._ultima_checagem < self.cfg.checar_chamada_s:
            return
        self._ultima_checagem = agora
        app = em_chamada()
        if app and not self.app_em_chamada:
            log.info("Em chamada (%s): soltando a câmera", app)
            self._soltar_camera()  # libera a câmera para a reunião
        self.app_em_chamada = app

    def _contar_tempo(self, agora: float, vigiando: bool) -> None:
        self.monitor.contar_tempo(agora - self._ultimo_passo, vigiando)
        self._ultimo_passo = agora
        if agora - self._ultimo_salvamento > SALVAR_RECORDE_S:
            self.historico.salvar_recorde(self.dia, self.monitor.recorde_s)
            self._ultimo_salvamento = agora

    def _passo(self) -> None:
        agora = time.monotonic()
        self._virada_do_dia()
        self._checar_chamada(agora)
        if self.pausado or self.app_em_chamada:
            self._contar_tempo(agora, vigiando=False)
            return
        self.camera_ocupada = not self.camera.abrir()
        frame = None if self.camera_ocupada else self.camera.ler()
        if frame is None:
            self._contar_tempo(agora, vigiando=False)
            return
        self._contar_tempo(agora, vigiando=True)
        self.foco.atualizar()

        analise = self.detector.analisar(frame)
        decisao = self.decisor.decidir(analise.mao) if analise and analise.mao else None
        tipo = self.monitor.registrar_quadro(bool(decisao and decisao.na_boca), agora)
        if tipo:
            self._alertar(tipo)
        if self.cfg.preview:
            self._mostrar_preview(frame, analise, decisao)
        # 'frame' sai de escopo aqui: nenhuma imagem é gravada

    def _mostrar_preview(self, frame, analise, decisao) -> None:
        texto = "sem mao/rosto" if decisao is None else f"valor: {decisao.valor:.2f}"
        cv2.imshow("preview (q fecha)", desenhar(frame, analise, texto, bool(decisao and decisao.na_boca)))
        if cv2.waitKey(1) & 0xFF == ord("q"):
            self.cfg.preview = False
            cv2.destroyAllWindows()

    def _tique(self) -> None:
        while not self.fila.empty():
            self.fila.get_nowait()()
        if self.saindo:
            return
        try:
            self._passo()
            self._atualizar_interface()
        except Exception:  # um erro pontual não pode derrubar o app
            log.exception("Erro no ciclo de detecção")
        self.root.after(int(1000 / self.cfg.fps), self._tique)

    def rodar(self) -> None:
        self.bandeja.iniciar()
        if self.cfg.testar_alerta:
            self.root.after(800, self.testar_alerta)
        self.root.after(200, self._tique)
        self.root.mainloop()
