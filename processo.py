
# -*- coding: utf-8 -*-
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Optional

USER_QUANTUM_MS: Dict[int, int] = {1: 6, 2: 5, 3: 4, 4: 3, 5: 2}
MAX_QUEUE_SIZE = 100
AGING_THRESHOLD_TICKS = 3  # ciclos sem executar => sobe prioridade (min 1)

@dataclass
class Processo:
    pid: int
    start: int                  # tempo de inicialização (tempo_init)
    init_priority: int           # 0 (tempo real), 1..5 (usuário)
    cpu_time: int                # tempo total de CPU em ticks
    mem_blocks: int              # blocos de memória solicitados
    printer_id: int              # 0 = não usa, 1–2 = impressora
    scanner_req: int             # 0/1
    modem_req: int               # 0/1
    sata_id: int                 # 0 = não usa, 1–3 = SATA

    current_priority: int = field(init=False)
    remaining_cpu: int = field(init=False)
    remaining_init: int = field(init=False)
    aging_counter: int = field(default=0, repr=False)
    offset: int = field(default=-1)  # posição inicial na memória

    req_printer= None
    req_scanner= None
    req_sata= None
    req_modem= None

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

    def aloca_recursos(self, printer=None, scanner=None, sata=None, modem=None):
        self.req_printer = printer
        self.req_scanner = scanner
        self.req_sata = sata
        self.req_modem = modem

    def __post_init__(self):
        self.current_priority = self.init_priority
        self.remaining_cpu = self.cpu_time
        self.remaining_init = self.start

    @property
    def is_real_time(self) -> bool:
        return self.init_priority == 0

    def __str__(self):
        return f"P{self.pid}(prio={self.current_priority}, rem={self.remaining_cpu})"

    def age(self, tempo: int):
        if (self.aging_counter + 1) > 6:
            self.aging_counter = (self.aging_counter + tempo) % 6
            self.current_priority = max(self.current_priority, 1)

        else:
            self.aging_counter = (self.aging_counter + tempo) % 6

    def tempo_user(self, tempo: int):
        self.remaining_init = max(self.remaining_init - tempo, 0)

    def tempo_rt(self, tempo: int):
        self.remaining_init = max(self.remaining_init - tempo, 0)
