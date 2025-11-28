# -*- coding: utf-8 -*-
from typing import List, Optional, Dict

class FileManager:
    def __init__(self, total_blocks: int):
        self.total_blocks = total_blocks                         # Numero total de blocos disponiveis no sistema
        self.blocks: List[Optional[str]] = [None] * total_blocks # Lista que representa os blocos, inicialmente todos livres (None)
        self.files: Dict[str, Dict] = {}                         # Dicionario que mapeia nome do arquivo -> informacoes (offset, tamanho, criador)

    def load_existing(self, existing: List[tuple]):
        # Carrega arquivos ja existentes no sistema
        for name, offset, size, creator in existing:
            # Marca os blocos ocupados pelo arquivo
            for i in range(offset, offset + size):
                self.blocks[i] = name
            # Registra informacoes do arquivo
            self.files[name] = {"offset": offset, "size": size, "creator": creator}

    def create(self, pid: int, name: str, size: int, is_real_time: bool) -> bool:
        # Cria um novo arquivo ocupando blocos contiguos
        free_count = 0
        offset = None
        # Busca espaco livre suficiente
        for i in range(self.total_blocks):
            if self.blocks[i] is None:
                free_count += 1
                if free_count == size:
                    offset = i - size + 1
                    break
            else:
                free_count = 0

        if offset is None:
            return False  # nao ha espaco suficiente

        # Marca blocos como ocupados pelo arquivo
        for j in range(offset, offset + size):
            self.blocks[j] = name
        # Registra informacoes do arquivo
        self.files[name] = {"offset": offset, "size": size, "creator": pid}
        return True

    def delete(self, pid: int, name: str, is_real_time: bool) -> bool:
        # Remove um arquivo do sistema
        if name not in self.files:
            return False

        creator = self.files[name]["creator"]
        # Verifica permissao: usuario comum nao pode deletar arquivo de outro
        if not is_real_time and creator != pid:
            return False

        # Libera blocos ocupados pelo arquivo
        offset = self.files[name]["offset"]
        size = self.files[name]["size"]
        for j in range(offset, offset + size):
            self.blocks[j] = None
        # Remove registro do arquivo
        del self.files[name]
        return True

    def show_map(self) -> str:
        # Retorna representacao dos blocos: nome do arquivo ou "0" se livre
        return "".join(b if b is not None else "0" for b in self.blocks)
