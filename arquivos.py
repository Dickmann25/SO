# -*- coding: utf-8 -*-
from typing import List, Optional, Dict

class FileManager:
    def __init__(self, total_blocks: int):
        self.total_blocks = total_blocks
        self.blocks: List[Optional[str]] = [None] * total_blocks
        # Mapeia arquivo -> (offset, tamanho, criador)
        self.files: Dict[str, Dict] = {}

    def load_existing(self, existing: List[tuple]):
        """
        Carrega arquivos ja existentes no disco.
        existing: lista de (nome, offset, tamanho, criador)
        """
        for name, offset, size, creator in existing:
            for i in range(offset, offset + size):
                self.blocks[i] = name
            self.files[name] = {"offset": offset, "size": size, "creator": creator}

    def create(self, pid: int, name: str, size: int, is_real_time: bool) -> bool:
        """Cria arquivo com alocacao contigua first-fit."""
        free_count = 0
        offset = None
        for i in range(self.total_blocks):
            if self.blocks[i] is None:
                free_count += 1
                if free_count == size:
                    offset = i - size + 1
                    break
            else:
                free_count = 0

        if offset is None:
            return False  # nao ha espaco

        # marca blocos
        for j in range(offset, offset + size):
            self.blocks[j] = name
        self.files[name] = {"offset": offset, "size": size, "creator": pid}
        return True

    def delete(self, pid: int, name: str, is_real_time: bool) -> bool:
        """Deleta arquivo se permitido."""
        if name not in self.files:
            return False

        creator = self.files[name]["creator"]
        if not is_real_time and creator != pid:
            return False  # usuario nao pode deletar arquivo de outro

        offset = self.files[name]["offset"]
        size = self.files[name]["size"]
        for j in range(offset, offset + size):
            self.blocks[j] = None
        del self.files[name]
        return True

    def show_map(self) -> str:
        """Retorna string com mapa do disco (nome ou 0)."""
        return "".join(b if b is not None else "0" for b in self.blocks)

