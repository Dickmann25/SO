from processo import Processo
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Optional

# Dicionario que define o quantum de tempo em ms para cada usuario
USER_QUANTUM_MS: Dict[int, int] = {1: 6, 2: 5, 3: 4, 4: 3, 5: 2}

# Tamanho maximo permitido para a fila
MAX_QUEUE_SIZE = 100

class Fila:
    def __init__(self, name: str, capacity: int = MAX_QUEUE_SIZE):
        self.name = name # Nome da fila
        self.capacity = capacity # Capacidade maxima da fila
        self.q: Deque[Processo] = deque() # Estrutura de dados deque para armazenar processos

    def push(self, proc: Processo) -> bool:
        # Adiciona um processo na fila se houver espaco
        if len(self.q) >= self.capacity:
            return False
        self.q.append(proc)
        return True

    def pop(self) -> Optional[Processo]:
        # Remove e retorna o primeiro processo da fila
        return self.q.popleft() if self.q else None

    def peek(self) -> Optional[Processo]:
        # Retorna o primeiro processo sem remover
        return self.q[0] if self.q else None

    def incrementar_tempo_espera(self, tempo):
        # Incrementa o tempo de espera de todos os processos na fila
        for proc in self.q:
            # Se o processo ainda nao iniciou, atualiza tempo de usuario
            if proc.remaining_init != 0:
                proc.tempo_init(tempo)
            # Atualiza idade do processo
            if proc.init_priority != 0:
                proc.age(tempo)

    def __len__(self):
        # Retorna quantidade de processos na fila
        return len(self.q)

    def __iter__(self):
        # Permite iterar sobre os processos da fila
        return iter(self.q)
