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
    # Arquivos de entrada
    process_file = "processes.txt"
    fileops_file = "files.txt"

    semaforo_processos = threading.Semaphore(1)   # controla acesso a fila de processos
    semaforo_memoria = threading.Semaphore(1)     # controla acesso a memoria


    # Inicializa os modulos necessarios
    recursos = Recursos()
    memoria = MemoryManager()
    escalanador = Escalonador(memoria, recursos, semaforo_processos, semaforo_memoria)

    # passa o escalonador para o dispatcher
    dispatcher = Despachador(escalanador, memoria, process_file, fileops_file, semaforo_processos, semaforo_memoria)

    # cria uma thread para rodar o escalonador
    t_escalonador = threading.Thread(target=escalanador.main, daemon=True)
    t_escalonador.start()

    dispatcher.load_processes()
    dispatcher.load_filesystem()
    dispatcher.criar_processo()

    while dispatcher.has_pending() or escalanador.has_ready():
        dispatcher.criar_processo()
        time.sleep(0.1)  # pequeno intervalo para nao travar a CPU

if __name__ == "__main__":
    main()