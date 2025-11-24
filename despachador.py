
from processo import Processo
from memoria import MemoryManager
from typing import List
from arquivos import FileManager

class Despachador:
    def __init__(self, escalonador, memoria, processos, arquivos):
        self.process_file = processos
        self.fileops_file = arquivos

        self.processos_pendentes = [] 
        self.processes = []
        self.memoria = memoria
        self.pid = 0
        self.escalonador = escalonador
        self.proc_existentes = []

    def load_processes(self):
        with open(self.process_file) as f:
            lines = [line.strip() for line in f if line.strip()]
        for pid, line in enumerate(lines):
            # formato: <tempo_init>, <prioridade>, <tempo_cpu>, <blocos_mem>, <printer>, <scanner>, <modem>, <sata>
            parts = list(map(int, line.split(",")))
            tempo_inicio, prioridade, tempo_cpu, blocos_mem, printer_code, scanner_req, modem_req, sata_code = parts
            self.processes.append((tempo_inicio, prioridade, tempo_cpu,
                              blocos_mem, printer_code, scanner_req,
                              modem_req, sata_code))

    def load_filesystem(self):
        with open(self.fileops_file) as f:
            lines = [line.strip() for line in f if line.strip()]
        total_blocks = int(lines[0])
        n_segments = int(lines[1])
        fm = FileManager(total_blocks)
        # carregar segmentos existentes
        for i in range(2, 2 + n_segments):
            name, offset, size = lines[i].split(",")
            fm.load_existing([(name.strip(), int(offset), int(size), 0)])
        self.file_manager = fm
        # operacões
        self.file_ops = []
        for line in lines[2 + n_segments:]:
            parts = line.split(",")
            pid = int(parts[0])
            op = int(parts[1])
            name = parts[2].strip()
            size = int(parts[3]) if op == 0 else None
            self.file_ops.append((pid, op, name, size))

    def has_pending(self):
        return len(self.processos_pendentes) > 0 or len(self.relacao_processos) > 0

    def criar_processo(self):
        self.relacao_processos =    self.processes

        while(self.relacao_processos or self.processos_pendentes):
            contador = 0
            for tempo_inicio, prioridade, tempo_cpu, blocos_mem, printer_code, scanner_req, modem_req, sata_code in self.processos_pendentes.copy():
                logs: List[str] = []
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

                    logs.append("dispatcher =>")
                    logs.append(f"PID: {proc.pid}")
                    logs.append(f"offset: {proc.mem_offset}")
                    logs.append(f"blocks: {proc.mem_blocks}")
                    logs.append(f"priority: {proc.init_priority}")
                    logs.append(f"time: {proc.cpu_time}")
                    logs.append(f"scanners: {proc.scanner_req}")
                    logs.append(f"printers: {proc.printer_id}")
                    logs.append(f"modems: {proc.modem_req}")
                    logs.append(f"sata: {proc.sata_id}")
                    logs.append("\n")
                    temp = "\n".join(logs)
                    print(temp)

                    del self.processos_pendentes[contador]
                    self.proc_existentes.append(proc)
                    self.escalonador.processos.put(proc)

                    self.pid+=1
                    contador-=1
                contador+=1
            
            for tempo_inicio, prioridade, tempo_cpu, blocos_mem, printer_code, scanner_req, modem_req, sata_code in self.relacao_processos.copy():
                logs: List[str] = []
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

                    logs.append("dispatcher =>")
                    logs.append(f"PID: {proc.pid}")
                    logs.append(f"offset: {proc.mem_offset}")
                    logs.append(f"blocks: {proc.mem_blocks}")
                    logs.append(f"priority: {proc.init_priority}")
                    logs.append(f"time: {proc.cpu_time}")
                    logs.append(f"scanners: {proc.scanner_req}")
                    logs.append(f"printers: {proc.printer_id}")
                    logs.append(f"modems: {proc.modem_req}")
                    logs.append(f"sata: {proc.sata_id}")
                    logs.append("\n")
                    temp = "\n".join(logs)
                    print(temp)

                    del self.relacao_processos[contador]
                    self.proc_existentes.append(proc)
                    self.escalonador.processos.put(proc)
                    self.pid+=1
                    contador-=1
                contador+=1 
        
        self.escalonador.despachador_finalizado = True
        logs: List[str] = []
        logs.append("\nSistema de arquivos =>")
        for i, (pid, op, name, size) in enumerate(self.file_ops, start=1):
            temp = []
            proc = next((p for p in self.proc_existentes if p.pid == pid), None)
            if proc is None:
                logs.append(f"Operacao {i} => Falha\nO processo {pid} nao existe.")
                continue
            if op == 0:  # criar
                ok = self.file_manager.create(proc.pid, name, size, proc.is_real_time)
                if ok:
                    logs.append(f"Operacao {i} => Sucesso\nO processo {pid} criou o arquivo {name}.")
                else:
                    logs.append(f"Operacao {i} => Falha\nO processo {pid} nao pode criar o arquivo {name} (falta de espaco).")
            else:  # deletar
                ok = self.file_manager.delete(proc.pid, name, proc.is_real_time)
                if ok:
                    logs.append(f"Operacao {i} => Sucesso\nO processo {pid} deletou o arquivo {name}.")
                else:
                    logs.append(f"Operacao {i} => Falha\nO processo {pid} nao pode deletar o arquivo {name}.")
        logs.append("\nMapa de ocupacao do disco:")
        logs.append(self.file_manager.show_map())
        temp = "\n".join(logs)
        while self.escalonador.finalizado == False:
            continue
        print(temp)





