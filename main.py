# main.py
import time
import threading
from despachador import Despachador
from recursos import Recursos
from dados import dados_processos
from escalonador import Escalonador
from memoria import MemoryManager
from arquivos import FileManager

def main():
    # Arquivos padrão para debug
    process_file = "processes.txt"
    fileops_file = "files.txt"

    recursos = Recursos()
    memoria = MemoryManager()
    escalanador = Escalonador(memoria, recursos)

    # passa o escalonador para o dispatcher
    dispatcher = Despachador(escalanador, memoria, process_file, fileops_file)

    # cria uma thread para rodar o escalonador
    t_escalonador = threading.Thread(target=escalanador.main, daemon=True)
    t_escalonador.start()

    dispatcher.load_processes()
    dispatcher.load_filesystem()
    dispatcher.criar_processo()

    while dispatcher.has_pending() or escalanador.has_ready():
        dispatcher.criar_processo()
        time.sleep(0.1)  # pequeno intervalo para não travar a CPU

if __name__ == "__main__":
    main()