# -*- coding: utf-8 -*-
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Optional
from fila import Fila
from processo import Processo
from memoria import MemoryManager
import queue

USER_QUANTUM_MS: Dict[int, int] = {1: 6, 2: 5, 3: 4, 4: 3, 5: 2}
MAX_QUEUE_SIZE = 100
AGING_THRESHOLD_TICKS = 3

class Escalonador:
    def __init__(self, memoria, recursos):
        self.rt_queue = Fila("RT")
        self.user_queues: Dict[int, Fila] = {p: Fila(f"U{p}") for p in range(1, 6)}
        self.tick_count = 0
        self.processos = queue.Queue() 
        self.memoria = memoria
        self.recursos = recursos
        self.finalizado = False
        self.despachador_finalizado = False

    def has_ready(self) -> bool:
        return len(self.rt_queue) > 0 or any(len(self.user_queues[p]) > 0 for p in range(1, 6))

    def adiciona_fila(self, proc: Processo):
        if proc.init_priority == 0:
            return self.rt_queue.push(proc)
        prio = min(max(proc.current_priority, 1), 5)
        return self.user_queues[prio].push(proc)

    def proximo_processo(self) -> Optional[Processo]:
        # RT tem precedência absoluta
        proc = self.rt_queue.pop()
        if proc:
            if proc.remaining_init == 0:
                return proc
            else:
                proc_temp = self.proximo_processo()
                self.rt_queue.push(proc)
                return proc_temp

        # Escolhe a fila de maior prioridade (número menor)
        for prio in range(1, 6):
            proc = self.user_queues[prio].pop()
            
            if proc != None:
                if proc.remaining_init == 0:
                    request = proc.checa_recursos()
                    if request == False:
                        request = self.recursos.request(proc, proc.pid, proc.scanner_req, proc.printer_id, proc.modem_req, proc.sata_id)
                        if request == False:
                            proc_temp = self.proximo_processo()
                            self.user_queues[prio].push(proc)
                            return proc_temp
                else:
                    proc_temp = self.proximo_processo()
                    self.user_queues[prio].push(proc)
                    return proc_temp


            if proc:
                return proc
        return None

    def run_one_slice(self, proc: Processo) -> str:
        logs: List[str] = []
        request = 0

        if proc.is_real_time:
            logs.append(f"\nExecutando {proc}")
            while proc.remaining_cpu > 0:
                logs.append(f"{proc} instruction {proc.cpu_time - proc.remaining_cpu + 1}")
                proc.remaining_cpu -= 1
                self.tick_count += 1
            logs.append(f"{proc} return SIGINT\n")
            self.memoria.free(proc.pid)
            logs.append(f"Processo P{proc.pid} concluido, memoria liberada")
            for fila in self.user_queues:
                self.user_queues[fila].incrementar_tempo_espera(self.tick_count)
            self.tick_count = 0
            if self.has_ready() != True and self.despachador_finalizado:
                self.finalizado = True
            return "\n".join(logs)

        quantum = USER_QUANTUM_MS[proc.current_priority]
        ran = 0
        
        request = proc.checa_recursos()
        if request == False:
            request = self.recursos.request(proc, proc.pid, proc.scanner_req, proc.printer_id, proc.modem_req, proc.sata_id)


        logs.append(f"\nExecutando {proc}")
        while ran < quantum and proc.remaining_cpu > 0:
            logs.append(f"{proc} instruction {proc.cpu_time - proc.remaining_cpu + 1}")
            proc.remaining_cpu -= 1
            self.tick_count += 1
            ran += 1

        if proc.remaining_cpu == 0:
            logs.append(f"{proc} return SIGINT")
            self.memoria.free(proc.pid)
            logs.append(f"Processo P{proc.pid} concluido, memoria liberada")
            self.recursos.release(proc, proc.pid)
            if self.has_ready() != True and self.despachador_finalizado:
                self.finalizado = True
            return "\n".join(logs)

        # Realimentação: não terminou → rebaixa (até 5), zera aging, reinsere
        if proc.current_priority < 5:
            proc.current_priority += 1
        proc.aging_counter = 0

        for fila in self.user_queues:
            self.user_queues[fila].incrementar_tempo_espera(self.tick_count)

        self.user_queues[proc.current_priority].push(proc)
        return "\n".join(logs)
        
    def main(self):
        while True:
            proc = None
            # consome todos os processos que chegaram
            while not self.processos.empty():
                proc = self.processos.get()
                print(f"[Escalonador] Recebi processo {proc}")
                self.adiciona_fila(proc)

            proc = self.proximo_processo()
            if proc != None:
                print(self.run_one_slice(proc))

            else:
                for fila in self.rt_queue:
                    self.rt_queue.incrementar_tempo_espera(1)

                for fila in self.user_queues:
                    self.user_queues[fila].incrementar_tempo_espera(1)
                continue
