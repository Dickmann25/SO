
# -*- coding: utf-8 -*-
from typing import List, Optional

TOTAL_BLOCKS = 1024
RT_BLOCKS = 64
USER_BLOCKS = TOTAL_BLOCKS - RT_BLOCKS

class MemoryManager:
    def __init__(self):
        # Representa cada bloco da memoria
        self.blocks: List[Optional[int]] = [None] * TOTAL_BLOCKS

    def allocate(self, pid: int, size: int, is_real_time: int) -> Optional[int]:
        """
        Aloca 'size' blocos contiguos para o processo 'pid'.
        Retorna o offset inicial ou None se nao couber.
        """
        if is_real_time == 0:
            start, end = 0, RT_BLOCKS
        else:
            start, end = RT_BLOCKS, TOTAL_BLOCKS

        # busca contigua (first-fit)
        free_count = 0
        offset = None
        for i in range(start, end):
            if self.blocks[i] is None:
                free_count += 1
                if free_count == size:
                    offset = i - size + 1
                    break
            else:
                free_count = 0

        if offset is None:
            return None  # nao coube

        # marca blocos como ocupados pelo pid
        for j in range(offset, offset + size):
            self.blocks[j] = pid
        return offset

    def free(self, pid: int):
        """Libera todos os blocos ocupados pelo processo 'pid'."""
        for i in range(TOTAL_BLOCKS):
            if self.blocks[i] == pid:
                self.blocks[i] = None
