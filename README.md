# Indução em Duto Metálico por Linha de Transmissão

Este projeto tem como objetivo calcular a tensão induzida em um duto metálico subterrâneo devido à indução eletromagnética provocada por uma linha de transmissão aérea ou subterrânea.

## Funcionalidades Atuais

- **Cálculo de Tensão Induzida:** O programa calcula a tensão induzida no duto, considerando o acoplamento indutivo e resistivo entre a linha de transmissão e o duto.
- **Condições de Operação:** Os cálculos podem ser realizados para condições normais de operação da linha de transmissão.
- **Análise de Travessia:** Atualmente, o foco principal está no cálculo da indução em situações de travessia, onde a linha de transmissão cruza o duto.

## Próximos Passos (Funcionalidades Futuras)

- Implementação de cálculos para condições de falta (curto-circuito) na linha de transmissão.
- Expansão para análise de paralelismo entre a linha de transmissão e o duto.
- Consideração de diferentes configurações de cabos e dutos.

## Como Usar

1.  **Configuração:** Defina as coordenadas (x, y) dos cabos da linha de transmissão e do duto, bem como as correntes que fluem pelos cabos.
2.  **Execução:** Execute o script `main.py` para realizar os cálculos.
3.  **Resultados:** O programa exibirá as características do duto, as impedâncias mútuas entre o duto e cada cabo, e a tensão total induzida no duto.

## Estrutura do Projeto

- `duto.py`: Contém as classes e métodos para modelar o duto, os cabos da linha de transmissão e realizar os cálculos de distância e impedância mútua.
- `main.py`: Ponto de entrada do programa, onde os objetos são instanciados e os cálculos são executados e exibidos.
- `constants.py`: Define constantes físicas utilizadas nos cálculos.
- `physical_constants.py`: (A ser implementado/utilizado para constantes físicas adicionais, se necessário).
