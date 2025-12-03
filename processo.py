# -*- coding: utf-8 -*-
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Optional

USER_QUANTUM_MS: Dict[int, int] = {1: 6, 2: 5, 3: 4, 4: 3, 5: 2}  # quantum de tempo por prioridade de usuario
MAX_QUEUE_SIZE = 100  # tamanho maximo da fila
AGING_THRESHOLD_TICKS = 3  # ciclos sem executar => sobe prioridade (min 1)

@dataclass
class Processo:
    pid: int  # identificador do processo
    start: int  # tempo de inicializacao (tempo_init)
    init_priority: int  # prioridade inicial: 0 (tempo real), 1..5 (usuario)
    cpu_time: int  # tempo total de CPU em ticks
    mem_blocks: int  # blocos de memoria solicitados
    printer_id: int  # 0 = nao usa, 1–2 = impressora
    scanner_req: int  # 0/1
    modem_req: int  # 0/1
    sata_id: int  # 0 = nao usa, 1–3 = SATA

    current_priority: int = field(init=False)  # prioridade atual
    remaining_cpu: int = field(init=False)  # tempo restante de CPU
    remaining_init: int = field(init=False)  # tempo restante de inicializacao
    aging_counter: int = field(default=0, repr=False)  # contador para envelhecimento
    offset: int = field(default=-1)  # posicao inicial na memoria

    req_printer = None  # recurso impressora alocado
    req_scanner = None  # recurso scanner alocado
    req_sata = None  # recurso sata alocado
    req_modem = None  # recurso modem alocado

    # Verifica se todos os recursos solicitados foram alocados
    def checa_recursos(self) -> bool:
        if self.printer_id != 0 and self.req_printer is None:
            return False
        if self.scanner_req == 1 and self.req_scanner is None:
            return False
        if self.modem_req == 1 and self.req_modem is None:
            return False
        if self.sata_id != 0 and self.req_sata is None:
            return False
        return True

    # Aloca recursos ao processo
    def aloca_recursos(self, printer=None, scanner=None, sata=None, modem=None):
        self.req_printer = printer
        self.req_scanner = scanner
        self.req_sata = sata
        self.req_modem = modem

    # Inicializa atributos apos criacao do objeto
    def __post_init__(self):
        self.current_priority = self.init_priority
        self.remaining_cpu = self.cpu_time
        self.remaining_init = self.start

    # Retorna se o processo e de tempo real
    @property
    def is_real_time(self) -> bool:
        return self.init_priority == 0

    # Representacao textual do processo
    def __str__(self):
        return f"P{self.pid}(prio={self.current_priority}, rem={self.remaining_cpu})"

    # Aplica envelhecimento ao processo
    def age(self, tempo: int):
        if (self.aging_counter + 1) > 6:
            self.aging_counter = (self.aging_counter + tempo) % 6
            self.current_priority = max(self.current_priority, 1)
        else:
            self.aging_counter = (self.aging_counter + tempo) % 6

    # Atualiza tempo de inicializacao para o processo
    def tempo_init(self, tempo: int):
        self.remaining_init = max(self.remaining_init - tempo, 0)


