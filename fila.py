from processo import Processo
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Optional

USER_QUANTUM_MS: Dict[int, int] = {1: 6, 2: 5, 3: 4, 4: 3, 5: 2}
MAX_QUEUE_SIZE = 100

class Fila:
    def __init__(self, name: str, capacity: int = MAX_QUEUE_SIZE):
        self.name = name
        self.capacity = capacity
        self.q: Deque[Processo] = deque()

    def push(self, proc: Processo) -> bool:
        if len(self.q) >= self.capacity:
            return False
        self.q.append(proc)
        return True

    def pop(self) -> Optional[Processo]:
        return self.q.popleft() if self.q else None

    def peek(self) -> Optional[Processo]:
        return self.q[0] if self.q else None

    def incrementar_tempo_espera(self, tempo):
        for proc in self.q:
            if proc.remaining_init != 0:
                proc.tempo_user(tempo)
            proc.age(tempo)

    def __len__(self):
        return len(self.q)

    def __iter__(self):
        return iter(self.q)
