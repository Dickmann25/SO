from processo import Processo        # Importa a classe Processo (representa um processo do sistema)
from memoria import MemoryManager    # Importa o gerenciador de memoria
from typing import List              # Importa suporte para tipagem de listas
from arquivos import FileManager     # Importa o gerenciador de arquivos


class Despachador:
    def __init__(self, escalonador, memoria, recursos, processos, arquivos, semaforo_processos, semaforo_memoria, semaforo_print):
        # Inicializa atributos do despachador
        self.process_file = processos          # Arquivo com lista de processos
        self.fileops_file = arquivos           # Arquivo com operacoes de arquivos
        self.processos_criados = 0             # Contador de processos criados
        self.processos_pendentes = []          # Lista de processos que nao puderam ser criados ainda
        self.processes = []                    # Lista de processos carregados do arquivo
        self.memoria = memoria                 # Referencia ao gerenciador de memoria
        self.recursos = recursos               # Referencia ao gerenciador de recursos
        self.pid = 0                           # Contador de PID (identificador unico de processo)
        self.escalonador = escalonador         # Referencia ao escalonador
        self.proc_existentes = []              # Lista de processos ja criados
        self.semaforo_processos = semaforo_processos    # Semaforo para controle da processos
        self.semaforo_memoria = semaforo_memoria    # Semaforo para controle da memoria
        self.semaforo_print = semaforo_print    # Semaforo para controle do print
        self.erro_arquivos = False             # Checa por erros criticos no sistema de arquivos

    def load_processes(self):
        contador = 0
        # Carrega os processos a partir do arquivo de entrada
        with open(self.process_file) as f:
            contador += 1
            lines = [line.strip() for line in f if line.strip()]  # Remove linhas vazias
        for pid, line in enumerate(lines):
            # Cada linha deve ter exatamente 8 valores inteiros separados por vírgula
            parts = line.split(",")
            if len(parts) != 8:
                # Linha fora do padrão é descartada
                with self.semaforo_print:
                    print(f"\n[ERROR] Linha {contador} do arquivo processes.txt fora do padrao, entrada {contador} foi descartada.")
                continue

            try:
                parts = list(map(int, parts))
            except ValueError:
                # Se não for possível converter todos para int, descarta
                with self.semaforo_print:
                    print(f"\n[ERROR] Linha {contador} do arquivo processes.txt contem valores nao inteiros, entrada {contador} foi descartada.")
                continue

            tempo_inicio, prioridade, tempo_cpu, blocos_mem, printer_code, scanner_req, modem_req, sata_code = parts

            # Verificacao de prioridade
            if prioridade < 0 or prioridade > 5:
                with self.semaforo_print:
                    print(f"\n[ERROR] Linha {contador} solicita prioridade {prioridade}, mas ela nao existe, entrada {contador} foi descartada.")
                continue

            # Verificação de tamanho de memória
            if prioridade == 0 and blocos_mem > 64:
                # Processo real não pode ter mais que 64 blocos
                with self.semaforo_print:
                    print(f"\n[ERROR] Processo de tempo real possui tamanho {blocos_mem}, mas o espaco de memoria reservado para processos de tempo real e 64, entrada {contador} foi descartada do arquivo processes.txt.")
                continue

            elif prioridade > 0 and blocos_mem > 960:
                # Processo de usuário não pode ter mais que 960 blocos
                with self.semaforo_print:
                    print(f"\n[ERROR] Processo de usuario possui tamanho {blocos_mem}, mas o espaco reservado de memoria reservado para processos de usuario e 960, entrada {contador} foi descartada do arquivo processes.txt.")
                continue

            if scanner_req > len([self.recursos.scanner]):  # só existe 1 scanner
                with self.semaforo_print:
                    print(f"\n[ERROR] Linha {contador} solicita scanner {scanner_req}, mas ele nao existe, entrada {contador} foi descartada.")
                continue

            if printer_code > len(self.recursos.printers):  # duas impressoras
                with self.semaforo_print:
                    print(f"\n[ERROR] Linha {contador} solicita impressora {printer_code}, mas ela nao existe, entrada {contador} foi descartada.")
                continue

            if modem_req > len([self.recursos.modem]):  # só existe 1 modem
                with self.semaforo_print:
                    print(f"\n[ERROR] Linha {contador} solicita modem {modem_req}, mas ele nao existe, entrada {contador} foi descartada.")
                continue

            if sata_code > len(self.recursos.sata):  # três portas SATA
                with self.semaforo_print:
                    print(f"\n[ERROR] Linha {contador} solicita dispositivo SATA{sata_code}, mas ele nao existe, entrada {contador} foi descartada.")
                continue

            # Adiciona processo à lista
            self.processes.append(
                (tempo_inicio, prioridade, tempo_cpu,
                 blocos_mem, printer_code, scanner_req,
                 modem_req, sata_code)
            )

    def load_filesystem(self):
        # Carrega configuração inicial do sistema de arquivos
        with open(self.fileops_file) as f:
            lines = [line.strip() for line in f if line.strip()]

        # Verifica se há pelo menos duas linhas
        if len(lines) < 2:
            with self.semaforo_print:
                print(f"\n[FATAL ERROR] Arquivo files.txt fora do padrao, sistema de arquivos nao executara")
            self.erro_arquivos = True
            return

        # Linha 1: número total de blocos
        try:
            total_blocks = int(lines[0])
            if total_blocks <= 0:
                raise ValueError("Numero de blocos invalido, negativo ou zero")

        except ValueError:
            with self.semaforo_print:
                print(f"\n[FATAL ERROR] Arquivo files.txt fora do padrao, sistema de arquivos nao executara")
            self.erro_arquivos = True
            return

        # Linha 2: número de segmentos
        try:
            n_segments = int(lines[1])
            if n_segments <= 0:
                raise ValueError("numero de segmentos invalido, negativo ou zero")

        except ValueError:
            with self.semaforo_print:
                print(f"\n[FATAL ERROR] Arquivo files.txt fora do padrao, sistema de arquivos nao executara")
            self.erro_arquivos = True
            return

        fm = FileManager(total_blocks)  # Cria gerenciador de arquivos

        # Conjunto de nomes já usados
        segmentos_existentes = set()

        # Lista de intervalos já ocupados (tuplas: (inicio, fim))
        espacos_ocupados = []

        for i in range(2, 2 + n_segments):
            try:
                name, offset, size = lines[i].split(",")
                name = name.strip()
                offset = int(offset)
                size = int(size)

                inicio = offset
                fim = offset + size - 1

                # Verifica se o espaço existe dentro do total_blocks
                if inicio < 0 or fim >= total_blocks:
                    with self.semaforo_print:
                        print(f"\n[FATAL ERROR] Segmento '{name}' ocupa espaco inexistente ({inicio}-{fim}), fora do limite de {total_blocks} blocos, sistema de arquivos nao executara")
                    self.erro_arquivos = True
                    return

                # Verifica duplicação de nome
                if name in segmentos_existentes:
                    with self.semaforo_print:
                        print(f"\n[FATAL ERROR] Segmento '{name}' duplicado no arquivo files.txt, sistema de arquivos nao executara")
                    self.erro_arquivos = True
                    return

                # Verifica sobreposição de intervalos
                for (ini, fim_existente) in espacos_ocupados:
                    if not (fim < ini or inicio > fim_existente):
                        # Há interseção
                        with self.semaforo_print:
                            print(f"\n[FATAL ERROR] Segmento '{name}' ocupa espaco ja utilizado ({inicio}-{fim}), sistema de arquivos nao executara")
                        self.erro_arquivos = True
                        return

                # Se passou nas verificações, adiciona
                fm.load_existing([(name, offset, size, 0)])
                segmentos_existentes.add(name)
                espacos_ocupados.append((inicio, fim))

            except Exception:
                with self.semaforo_print:
                    print(f"\n[FATAL ERROR] Arquivo files.txt fora do padrao, sistema de arquivos nao executara")
                self.erro_arquivos = True
                return

        self.file_manager = fm

        # Carrega operações de arquivos (criar/deletar)
        self.file_ops = []
        contador = 2 + n_segments
        for line in lines[2 + n_segments:]:
            contador += 1
            try:
                parts = line.split(",")
                pid = int(parts[0])        # Processo que fará a operação
                op = int(parts[1])         # Tipo de operação (0 = criar, 1 = deletar)
                name = parts[2].strip()    # Nome do arquivo
                size = int(parts[3]) if op == 0 else None  # Tamanho (apenas para criação)
                self.file_ops.append((pid, op, name, size))
            except Exception:
                # Se houver erro, descarta a linha
                with self.semaforo_print:
                    print(f"\n[ERROR] Linha {contador} do arquivo file.txt apresenta valores nao esperados, a operacao referente a linha {contador} foi descartada e nao sera executada")
                continue


    def has_pending(self):
        # Verifica se ainda existem processos pendentes ou nao despachados
        return len(self.processos_pendentes) > 0 or len(self.relacao_processos) > 0

    def criar_processo(self):
        # Inicializa lista de processos a despachar
        self.relacao_processos = self.processes
        limite = self.escalonador.capacity

        # Enquanto houver processos a despachar ou pendentes, e nao tiver criado 100 processos
        while (self.relacao_processos or self.processos_pendentes) and self.processos_criados != limite:
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
                    dispatcher_info =[
                    "",
                    "dispatcher =>",
                    f"PID: {proc.pid}",
                    f"offset: {proc.mem_offset}",
                    f"blocks: {proc.mem_blocks}",
                    f"priority: {proc.init_priority}",
                    f"time: {proc.cpu_time}",
                    f"scanners: {proc.scanner_req}",
                    f"printers: {proc.printer_id}",
                    f"modems: {proc.modem_req}",
                    f"sata: {proc.sata_id}",
                    ]
                    temp = "\n".join(dispatcher_info)

                    with self.semaforo_print:
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
                    self.processos_pendentes.append((tempo_inicio, prioridade, tempo_cpu, blocos_mem, printer_code, scanner_req, modem_req, sata_code))
                    del self.relacao_processos[contador]
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
                    dispatcher_info =[
                    "",
                    "dispatcher =>",
                    f"PID: {proc.pid}",
                    f"offset: {proc.mem_offset}",
                    f"blocks: {proc.mem_blocks}",
                    f"priority: {proc.init_priority}",
                    f"time: {proc.cpu_time}",
                    f"scanners: {proc.scanner_req}",
                    f"printers: {proc.printer_id}",
                    f"modems: {proc.modem_req}",
                    f"sata: {proc.sata_id}",
                    ]
                    temp = "\n".join(dispatcher_info)
                    
                    with self.semaforo_print:
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
        if self.erro_arquivos != True:
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
                        logs.append(f"Operacao {i} => Falha\nO processo {pid} nao pode criar o arquivo {name} (arquivo duplicado ou falta de espaco).")
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

            with self.semaforo_print:
                print(temp)

        else:
            while self.escalonador.finalizado == False: 
                continue 

            with self.semaforo_print:
                print("\n[FATAL ERROR] Houve uma falha critica no sistema de arquivos, file.txt apresenta erros, sistema de arquivos nao foi executado.")
