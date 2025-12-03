
def dados_processos(path: str):
    processes = []
    with open(path, "r") as f:
        for line in f:
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 8:
                continue
            tempo_inicio = int(parts[0])
            prioridade = int(parts[1])
            tempo_cpu = int(parts[2])
            blocos_mem = int(parts[3])
            printer_code = int(parts[4])
            scanner_req = int(parts[5])
            modem_req = int(parts[6])
            sata_code = int(parts[7])
            processes.append((tempo_inicio, prioridade, tempo_cpu,
                              blocos_mem, printer_code, scanner_req,
                              modem_req, sata_code))
    return processes