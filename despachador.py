from processo import Processo        # Importa a classe Processo (representa um processo do sistema)
from memoria import MemoryManager    # Importa o gerenciador de memoria
from typing import List              # Importa suporte para tipagem de listas
from arquivos import FileManager     # Importa o gerenciador de arquivos


class Despachador:
    def __init__(self, escalonador, memoria, processos, arquivos, semaforo_processos, semaforo_memoria):
        # Inicializa atributos do despachador
        self.process_file = processos          # Arquivo com lista de processos
        self.fileops_file = arquivos           # Arquivo com operacoes de arquivos
        self.processos_criados = 0             # Contador de processos criados
        self.processos_pendentes = []          # Lista de processos que nao puderam ser criados ainda
        self.processes = []                    # Lista de processos carregados do arquivo
        self.memoria = memoria                 # Referencia ao gerenciador de memoria
        self.pid = 0                           # Contador de PID (identificador unico de processo)
        self.escalonador = escalonador         # Referencia ao escalonador
        self.proc_existentes = []              # Lista de processos ja criados
        self.semaforo_processos = semaforo_processos    # Semaforo para controle da processos
        self.semaforo_memoria = semaforo_memoria    # Semaforo para controle da memoria

    def load_processes(self):
        # Carrega os processos a partir do arquivo de entrada
        with open(self.process_file) as f:
            lines = [line.strip() for line in f if line.strip()]  # Remove linhas vazias
        for pid, line in enumerate(lines):
            # Cada linha tem o formato: tempo_init, prioridade, tempo_cpu, blocos_mem, printer, scanner, modem, sata
            parts = list(map(int, line.split(",")))
            tempo_inicio, prioridade, tempo_cpu, blocos_mem, printer_code, scanner_req, modem_req, sata_code = parts
            # Adiciona processo a lista
            self.processes.append(
                (tempo_inicio, prioridade, tempo_cpu,
                 blocos_mem, printer_code, scanner_req,
                 modem_req, sata_code)
            )

    def load_filesystem(self):
        # Carrega configuracao inicial do sistema de arquivos
        with open(self.fileops_file) as f:
            lines = [line.strip() for line in f if line.strip()]
        total_blocks = int(lines[0])   # Numero total de blocos do disco
        n_segments = int(lines[1])     # Numero de segmentos ja existentes
        fm = FileManager(total_blocks) # Cria gerenciador de arquivos

        # Carrega segmentos ja existentes no disco
        for i in range(2, 2 + n_segments):
            name, offset, size = lines[i].split(",")
            fm.load_existing([(name.strip(), int(offset), int(size), 0)])
        self.file_manager = fm

        # Carrega operacoes de arquivos (criar/deletar)
        self.file_ops = []
        for line in lines[2 + n_segments:]:
            parts = line.split(",")
            pid = int(parts[0])        # Processo que fara a operacao
            op = int(parts[1])         # Tipo de operacao (0 = criar, 1 = deletar)
            name = parts[2].strip()    # Nome do arquivo
            size = int(parts[3]) if op == 0 else None  # Tamanho (apenas para criacao)
            self.file_ops.append((pid, op, name, size))

    def has_pending(self):
        # Verifica se ainda existem processos pendentes ou nao despachados
        return len(self.processos_pendentes) > 0 or len(self.relacao_processos) > 0

    def criar_processo(self):
        # Inicializa lista de processos a despachar
        self.relacao_processos = self.processes

        # Enquanto houver processos a despachar ou pendentes, e nao tiver criado 100 processos
        while (self.relacao_processos or self.processos_pendentes) and self.processos_criados != 100:
            contador = 0

            # Tenta criar processos pendentes
            for tempo_inicio, prioridade, tempo_cpu, blocos_mem, printer_code, scanner_req, modem_req, sata_code in self.processos_pendentes.copy():
                logs: List[str] = []

                with self.semaforo_memoria: 
                    offset = self.memoria.allocate(self.pid, blocos_mem, prioridade)  # Aloca memoria

                if offset is None:
                    # Se nao conseguiu alocar memoria, continua pendente
                    continue
                else:
                    # Cria objeto Processo
                    proc = Processo(
                        pid=self.pid,
                        start=tempo_inicio,
                        init_priority=prioridade,
                        cpu_time=tempo_cpu,
                        mem_blocks=blocos_mem,
                        printer_id=printer_code,
                        scanner_req=scanner_req,
                        modem_req=modem_req,
                        sata_id=sata_code
                    )
                    proc.mem_offset = offset  # Define posicao na memoria

                    # Gera log do processo criado
                    logs.append("\ndispatcher =>")
                    logs.append(f"PID: {proc.pid}")
                    logs.append(f"offset: {proc.mem_offset}")
                    logs.append(f"blocks: {proc.mem_blocks}")
                    logs.append(f"priority: {proc.init_priority}")
                    logs.append(f"time: {proc.cpu_time}")
                    logs.append(f"scanners: {proc.scanner_req}")
                    logs.append(f"printers: {proc.printer_id}")
                    logs.append(f"modems: {proc.modem_req}")
                    logs.append(f"sata: {proc.sata_id}\n")
                    temp = "\n".join(logs)
                    print(temp)

                    with self.semaforo_processos:
                        # Remove da lista de pendentes e adiciona ao escalonador
                        del self.processos_pendentes[contador]
                        self.proc_existentes.append(proc)
                        self.escalonador.processos.put(proc)
                        self.processos_criados += 1
                        self.pid += 1
                        contador -= 1
                contador += 1

            # Tenta criar processos novos (nao pendentes)
            for tempo_inicio, prioridade, tempo_cpu, blocos_mem, printer_code, scanner_req, modem_req, sata_code in self.relacao_processos.copy():
                logs: List[str] = []

                with self.semaforo_memoria:
                    offset = self.memoria.allocate(self.pid, blocos_mem, prioridade)

                if offset is None:
                    continue
                else:
                    proc = Processo(
                        pid=self.pid,
                        start=tempo_inicio,
                        init_priority=prioridade,
                        cpu_time=tempo_cpu,
                        mem_blocks=blocos_mem,
                        printer_id=printer_code,
                        scanner_req=scanner_req,
                        modem_req=modem_req,
                        sata_id=sata_code
                    )
                    proc.mem_offset = offset

                    # Log do processo
                    logs.append("\ndispatcher =>")
                    logs.append(f"PID: {proc.pid}")
                    logs.append(f"offset: {proc.mem_offset}")
                    logs.append(f"blocks: {proc.mem_blocks}")
                    logs.append(f"priority: {proc.init_priority}")
                    logs.append(f"time: {proc.cpu_time}")
                    logs.append(f"scanners: {proc.scanner_req}")
                    logs.append(f"printers: {proc.printer_id}")
                    logs.append(f"modems: {proc.modem_req}")
                    logs.append(f"sata: {proc.sata_id}\n")
                    temp = "\n".join(logs)
                    print(temp)

                    with self.semaforo_processos:
                        # Remove da lista e adiciona ao escalonador
                        del self.relacao_processos[contador]
                        self.proc_existentes.append(proc)
                        self.escalonador.processos.put(proc)
                        self.processos_criados += 1
                        self.pid += 1
                        contador -= 1
                contador += 1

        # Marca que o despachador terminou
        self.escalonador.despachador_finalizado = True

        # Executa operacoes de arquivos
        logs: List[str] = []
        logs.append("\nSistema de arquivos =>")
        for i, (pid, op, name, size) in enumerate(self.file_ops, start=1):
            proc = next((p for p in self.proc_existentes if p.pid == pid), None)
            if proc is None:
                logs.append(f"Operacao {i} => Falha\nO processo {pid} nao existe.")
                continue
            if op == 0:  # Criar arquivo
                ok = self.file_manager.create(proc.pid, name, size, proc.is_real_time)
                if ok:
                    logs.append(f"Operacao {i} => Sucesso\nO processo {pid} criou o arquivo {name}.")
                else:
                    logs.append(f"Operacao {i} => Falha\nO processo {pid} nao pode criar o arquivo {name} (falta de espaco).")
            else:  # Deletar arquivo
                ok = self.file_manager.delete(proc.pid, name, proc.is_real_time)
                if ok:
                    logs.append(f"Operacao {i} => Sucesso\nO processo {pid} deletou o arquivo {name}.")
                else:
                    logs.append(f"Operacao {i} => Falha\nO processo {pid} nao pode deletar o arquivo {name}.")

        # Mostra mapa de ocupacao do disco
        logs.append("\nMapa de ocupacao do disco:")
        logs.append(self.file_manager.show_map())
        temp = "\n".join(logs)
        while self.escalonador.finalizado == False: 
            continue 
        
        print(temp)
