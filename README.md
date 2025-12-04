# Projeto de Sistemas Operacionais

Este projeto consiste na implementação de um **pseudo sistema operacional**, desenvolvido como trabalho acadêmico para a disciplina de Sistemas Operacionais. O objetivo é simular conceitos fundamentais como gerenciamento de processos, escalonamento, gerenciamento de memória, alocação de recursos e sistema de arquivos.

---

## Como executar o programa

A execução do projeto é simples:

1. Garanta que **todos os arquivos `.py`** estejam no **mesmo diretório**.
2. Abra um terminal no diretório do projeto.
3. Execute o arquivo principal:

```bash
python main.py
```
## Requisitos
Python 3.13.5 (recomendado para garantir a execução correta e compatibilidade total)


## Configuração das entradas
As entradas do sistema são definidas por arquivos de texto. Para modificar o comportamento do sistema, basta editar:

processes.txt: define os processos que serão criados e executados pelo sistema.

files.txt: define as operações e o estado inicial do sistema de arquivos.

Não é necessário alterar o código-fonte para modificar as entradas; todas as configurações podem ser ajustadas por meio desses arquivos .txt.

## Observações
O arquivo main.py é o ponto de entrada do sistema e responsável por inicializar as estruturas e iniciar o fluxo de execução.

O funcionamento correto do projeto depende da presença e integridade de todos os arquivos Python e de entrada no diretório.
