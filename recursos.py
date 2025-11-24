
# -*- coding: utf-8 -*-
from typing import Optional, Dict

class Recursos:
    def __init__(self):
        # Cada recurso é representado pelo PID que o ocupa ou None
        self.scanner: Optional[int] = None
        self.printers: Dict[int, Optional[int]] = {1: None, 2: None}
        self.modem: Optional[int] = None
        self.sata: Dict[int, Optional[int]] = {1: None, 2: None, 3: None}

    # ------------------------------
    # Alocacao
    # ------------------------------
    def request(self, proc,pid: int, scanner_req: int, printer_id: int,
                modem_req: int, sata_id: int) -> bool:
        """
        Tenta alocar recursos para o processo pid.
        Retorna True se todos foram alocados, False se algum nao disponivel.
        """

        # 1. Verificação de disponibilidade
        if scanner_req == 1 and self.scanner is not None:
            return False

        if printer_id in self.printers and printer_id != 0:
            if self.printers[printer_id] is not None:
                return False

        if modem_req == 1 and self.modem is not None:
            return False

        if sata_id in self.sata and sata_id != 0:
            if self.sata[sata_id] is not None:
                return False

        # 2. Se chegou aqui, todos estão livres efetiva a alocação
        if scanner_req == 1:
            self.scanner = pid
            proc.aloca_recursos(printer = proc.req_printer,scanner = 1, sata = proc.req_sata, modem = proc.req_modem)

        if printer_id in self.printers and printer_id != 0:
            self.printers[printer_id] = pid
            proc.aloca_recursos(printer = printer_id,scanner = proc.req_scanner, sata = proc.req_sata, modem = proc.req_modem)

        if modem_req == 1:
            self.modem = pid
            proc.aloca_recursos(printer = proc.req_printer,scanner = proc.req_scanner, sata = proc.req_sata, modem = 1)

        if sata_id in self.sata and sata_id != 0:
            self.sata[sata_id] = pid
            proc.aloca_recursos(printer = proc.req_printer,scanner = proc.req_scanner, sata = sata_id, modem = proc.req_modem)

        return True

    # ------------------------------
    # Liberacao
    # ------------------------------
    def release(self, proc, pid: int):
        """Libera todos os recursos ocupados por um processo."""
        if self.scanner == pid:
            self.scanner = None
        for k in self.printers:
            if self.printers[k] == pid:
                self.printers[k] = None
        if self.modem == pid:
            self.modem = None
        for k in self.sata:
            if self.sata[k] == pid:
                self.sata[k] = None
        proc.aloca_recursos()

