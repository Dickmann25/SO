# -*- coding: utf-8 -*-
from typing import Optional, Dict

class Recursos:
    def __init__(self):
        # Cada recurso e representado pelo PID que o ocupa ou None
        self.scanner: Optional[int] = None  # scanner unico
        self.printers: Dict[int, Optional[int]] = {1: None, 2: None}  # duas impressoras
        self.modem: Optional[int] = None  # modem unico
        self.sata: Dict[int, Optional[int]] = {1: None, 2: None, 3: None}  # tres portas sata

    # Solicita recursos para um processo
    def request(self, proc, pid: int, scanner_req: int, printer_id: int,
                modem_req: int, sata_id: int) -> bool:

        if scanner_req == 1 and self.scanner is not None:
            return False  # scanner ja ocupado

        if printer_id in self.printers and printer_id != 0:
            if self.printers[printer_id] is not None:
                return False  # impressora ja ocupada

        if modem_req == 1 and self.modem is not None:
            return False  # modem ja ocupado

        if sata_id in self.sata and sata_id != 0:
            if self.sata[sata_id] is not None:
                return False  # porta sata ja ocupada

        # Aloca scanner
        if scanner_req == 1:
            self.scanner = pid  # scanner ocupado pelo processo
            proc.aloca_recursos(printer=proc.req_printer, scanner=1,
                                sata=proc.req_sata, modem=proc.req_modem)

        # Aloca impressora
        if printer_id in self.printers and printer_id != 0:
            self.printers[printer_id] = pid  # impressora ocupada pelo processo
            proc.aloca_recursos(printer=printer_id, scanner=proc.req_scanner,
                                sata=proc.req_sata, modem=proc.req_modem)

        # Aloca modem
        if modem_req == 1:
            self.modem = pid  # modem ocupado pelo processo
            proc.aloca_recursos(printer=proc.req_printer, scanner=proc.req_scanner,
                                sata=proc.req_sata, modem=1)

        # Aloca porta sata
        if sata_id in self.sata and sata_id != 0:
            self.sata[sata_id] = pid  # porta sata ocupada pelo processo
            proc.aloca_recursos(printer=proc.req_printer, scanner=proc.req_scanner,
                                sata=sata_id, modem=proc.req_modem)

        return True

    # Libera recursos ocupados por um processo
    def release(self, proc, pid: int):
        if self.scanner == pid:
            self.scanner = None  # libera scanner
        for k in self.printers:
            if self.printers[k] == pid:
                self.printers[k] = None  # libera impressora
        if self.modem == pid:
            self.modem = None  # libera modem
        for k in self.sata:
            if self.sata[k] == pid:
                self.sata[k] = None  # libera porta sata
        proc.aloca_recursos()  # atualiza estado do processo
