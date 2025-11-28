# -*- coding: utf-8 -*-
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Optional
from fila import Fila
from processo import Processo
from memoria import MemoryManager
import queue

# Quantum de tempo para cada fila de usuario (em ms)
USER_QUANTUM_MS: Dict[int, int] = {1: 6, 2: 5, 3: 4, 4: 3, 5: 2}
MAX_QUEUE_SIZE = 100
AGING_THRESHOLD_TICKS = 3


class Escalonador:
    def __init__(self, memoria, recursos, semaforo_processos, semaforo_memoria):
        # Fila de processos de tempo real (RT)
        self.rt_queue = Fila("RT")
        # Filas de usuario, uma para cada prioridade (1 a 5)
        self.user_queues: Dict[int, Fila] = {p: Fila(f"U{p}") for p in range(1, 6)}
        self.tick_count = 0                     # Contador de ticks (tempo)
        self.processos = queue.Queue()          # Fila de processos criados pelo despachador
        self.memoria = memoria                  # Gerenciador de memoria
        self.recursos = recursos                # Gerenciador de recursos (scanner, impressora, etc.)
        self.finalizado = False                 # Flag para indicar fim da execucao
        self.despachador_finalizado = False     # Flag para indicar fim do despachador
        self.semaforo_processos = semaforo_processos    # Semaforo para controle da processos
        self.semaforo_memoria = semaforo_memoria    # Semaforo para controle da memoria

    # Checa se existem processos prontos para serem executados
    def has_ready(self) -> bool:
        return len(self.rt_queue) > 0 or any(len(self.user_queues[p]) > 0 for p in range(1, 6))

    # Adiciona os processos criados na fila de prioridade correta
    def adiciona_fila(self, proc: Processo):
        if proc.init_priority == 0:             # Se prioridade inicial = 0, vai para fila RT
            return self.rt_queue.push(proc)
        prio = min(max(proc.current_priority, 1), 5)  # Garante que prioridade esteja entre 1 e 5
        return self.user_queues[prio].push(proc)

    # Escolhe o proximo processo para ser executado
    def proximo_processo(self) -> Optional[Processo]:
        # RT tem precedencia absoluta
        proc = self.rt_queue.pop()
        if proc:
            if proc.remaining_init == 0:        # Se ja inicializado, retorna
                return proc
            else:                               # Se nao inicializado, tenta outro processo
                proc_temp = self.proximo_processo()
                self.rt_queue.push(proc)        # Reinsere na fila
                return proc_temp

        # Escolhe a fila de maior prioridade (numero menor)
        for prio in range(1, 6):
            proc = self.user_queues[prio].pop()

            # Checa se o processo esta inicializado
            if proc is not None:
                if proc.remaining_init == 0:
                    # Checa se os recursos necessarios estao disponiveis
                    request = proc.checa_recursos()
                    if request is False:
                        request = self.recursos.request(
                            proc,
                            proc.pid,
                            proc.scanner_req,
                            proc.printer_id,
                            proc.modem_req,
                            proc.sata_id
                        )
                        if request is False:    # Se nao conseguiu recursos, tenta outro processo
                            proc_temp = self.proximo_processo()
                            self.user_queues[prio].push(proc)  # Reinsere na fila
                            return proc_temp
                else:                           # Se nao inicializado, tenta outro processo
                    proc_temp = self.proximo_processo()
                    self.user_queues[prio].push(proc)
                    return proc_temp

            if proc:
                return proc
        return None

    # Executa um processo por um "slice" de tempo
    def run_one_slice(self, proc: Processo) -> str:
        logs: List[str] = []
        request = 0

        # Fluxo de processo de tempo real
        if proc.is_real_time:
            logs.append(f"\nExecutando {proc}")
            while proc.remaining_cpu > 0:       # Executa ate terminar
                logs.append(f"{proc} instruction {proc.cpu_time - proc.remaining_cpu + 1}")
                proc.remaining_cpu -= 1
                self.tick_count += 1
            logs.append(f"{proc} return SIGINT")

            with self.semaforo_memoria:
                self.memoria.free(proc.pid)         # Libera memoria
            logs.append(f"Processo P{proc.pid} concluido, memoria liberada")

            # Aging: incrementa tempo de espera nas filas
            self.rt_queue.incrementar_tempo_espera(self.tick_count)
            for fila in self.user_queues:
                self.user_queues[fila].incrementar_tempo_espera(self.tick_count)
            self.tick_count = 0

            # Se nao ha mais processos e despachador terminou, marca finalizado
            if self.has_ready() is not True and self.despachador_finalizado:
                self.finalizado = True

            return "\n".join(logs)

        # Fluxo de processo de usuario
        quantum = USER_QUANTUM_MS[proc.current_priority]  # Quantum depende da prioridade
        ran = 0

        logs.append(f"\nExecutando {proc}")
        while ran < quantum and proc.remaining_cpu > 0:   # Executa ate quantum ou fim
            logs.append(f"{proc} instruction {proc.cpu_time - proc.remaining_cpu + 1}")
            proc.remaining_cpu -= 1
            self.tick_count += 1
            ran += 1

        # Se terminou
        if proc.remaining_cpu == 0:
            logs.append(f"{proc} return SIGINT")

            with self.semaforo_memoria:
                self.memoria.free(proc.pid)

            logs.append(f"Processo P{proc.pid} concluido, memoria liberada")
            self.recursos.release(proc, proc.pid)

            if self.has_ready() is not True and self.despachador_finalizado:
                self.finalizado = True
            
            self.rt_queue.incrementar_tempo_espera(self.tick_count)
            for fila in self.user_queues:
                self.user_queues[fila].incrementar_tempo_espera(self.tick_count)

            return "\n".join(logs)

        # Se nao terminou: rebaixa prioridade (ate 5), zera aging e reinsere
        if proc.current_priority < 5:
            proc.current_priority += 1
        proc.aging_counter = 0

        # Aging: incrementa tempo de espera nas filas
        self.rt_queue.incrementar_tempo_espera(self.tick_count)
        for fila in self.user_queues:
            self.user_queues[fila].incrementar_tempo_espera(self.tick_count)

        self.user_queues[proc.current_priority].push(proc)
        return "\n".join(logs)

    # Loop principal do escalonador
    def main(self):
        while True:
            proc = None

            # Adiciona processos criados pelo despachador nas filas
            with self.semaforo_processos:
                while not self.processos.empty():
                    proc = self.processos.get()
                    self.adiciona_fila(proc)

            # Executa um processo
            proc = self.proximo_processo()
            if proc is not None:
                print(self.run_one_slice(proc))

            # Se nao ha processo pronto, aplica aging
            else:
                # Aging para fila RT
                self.rt_queue.incrementar_tempo_espera(1)

                # Aging para filas de usuario
                for fila in self.user_queues:
                    self.user_queues[fila].incrementar_tempo_espera(1)
                continue
