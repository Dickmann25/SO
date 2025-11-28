# -*- coding: utf-8 -*-
from typing import List, Optional

TOTAL_BLOCKS = 1024  # numero total de blocos de memoria
RT_BLOCKS = 64       # blocos reservados para processos de tempo real
USER_BLOCKS = TOTAL_BLOCKS - RT_BLOCKS  # blocos reservados para usuarios comuns

class MemoryManager:
    def __init__(self):
        self.blocks: List[Optional[int]] = [None] * TOTAL_BLOCKS  # lista que representa cada bloco da memoria

    # Aloca blocos de memoria para um processo usando algoritmo first-fit
    def allocate(self, pid: int, size: int, is_real_time: int) -> Optional[int]:
        if is_real_time == 0:
            start, end = 0, RT_BLOCKS  # tempo real usa blocos iniciais
        else:
            start, end = RT_BLOCKS, TOTAL_BLOCKS  # usuario comum usa blocos restantes

        free_count = 0  # contador de blocos livres contiguos
        offset = None   # posicao inicial da alocacao
        for i in range(start, end):
            if self.blocks[i] is None:  # bloco livre
                free_count += 1
                if free_count == size:  # encontrou espaco suficiente
                    offset = i - size + 1
                    break
            else:
                free_count = 0  # reinicia contagem se bloco ocupado

        if offset is None:
            return None  # nao ha espaco suficiente

        for j in range(offset, offset + size):
            self.blocks[j] = pid  # marca bloco como ocupado pelo processo
        return offset  # retorna posicao inicial da alocacao

    # Libera todos os blocos ocupados por um processo
    def free(self, pid: int):
        for i in range(TOTAL_BLOCKS):
            if self.blocks[i] == pid:  # libera blocos ocupados pelo processo
                self.blocks[i] = None
