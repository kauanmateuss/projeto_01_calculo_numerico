# Simulador de Propagação de Erros Numéricos

Projeto de Cálculo Numérico com calculadora de precisão limitada, comparação entre
truncamento e arredondamento e acompanhamento do erro em somas sucessivas.

## Executar

O ambiente virtual `.venv` já está instalado neste computador:

```bash
.venv/bin/python main.py
```

O menu de terminal e os exemplos também funcionam sem instalar PySide6:

```bash
python3 main.py --cli
python3 main.py --exemplos
```

Em outro computador, use Python 3.10+ e recrie o ambiente:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

Não copie `.venv` para outra máquina nem publique essa pasta no Git. No Debian/Ubuntu,
`python3 -m venv` pode exigir o pacote `python3-venv`. O ambiente desta máquina usa
Python 3.12, pois o Python padrão não tinha `ensurepip`.

## Organização

```text
projeto_erros/
├── main.py                    # Escolhe janela, terminal ou exemplos
├── backend/
│   ├── calculos.py            # Operações e sequência de somas
│   └── numeros.py             # Decimal, precisão e métricas
├── frontend/
│   ├── janela.py              # Formulários, páginas e eventos da janela
│   ├── componentes.py         # Cartões, tabelas e gráfico
│   ├── estilo.qss             # Cores, fontes e aparência
│   ├── apresentacao.py        # Formatação e exportação CSV
│   └── terminal.py            # Menu e exemplos no terminal
├── tests/
│   ├── test_backend.py        # Testes das regras numéricas
│   └── test_frontend.py       # Testes da janela e da exportação
├── docs/
│   ├── informacoes_trabalho_erros.pdf  # Enunciado original
│   └── relatorio_validacao.pdf        # Relatório da primeira revisão
├── requirements.txt          # Dependência da interface: PySide6
└── README.md
```

Cada pasta Python tem um `__init__.py` para identificá-la como pacote.
**O backend não importa o frontend nem o PySide6.** A janela e o terminal chamam
as mesmas funções, e somente a apresentação transforma os resultados em textos,
tabelas e gráficos. Não há classes, fábricas, controladores ou camadas de serviço
na lógica numérica: são funções, dicionários, condicionais e um laço de somas.

## Como explicar a lógica

Comece por `backend/calculos.py`, na função `calcular`:

1. Valida o número de dígitos e o método; converte x e y para `Decimal`.
2. Calcula a referência com os valores originais.
3. Se solicitado, limita os operandos e repete a operação com esses valores.
4. Limita o resultado e calcula o erro absoluto e o relativo.
5. Devolve um dicionário para a interface mostrar os resultados.

Depois leia `somar_sequencia`: o acumulador começa em zero; cada soma recebe
precisão limitada; a referência ideal de cada etapa é `valor × quantidade de termos`
e não depende das aproximações anteriores. O erro local mede a operação atual,
enquanto o erro acumulado compara o parcial com essa referência ideal.

Em `backend/numeros.py`, `ajustar_precisao` segue o enunciado: normaliza para
`0.dígitos × 10^expoente`, corta ou arredonda a mantissa e reconstrói o decimal.
Truncamento vai em direção ao zero; arredondamento resolve empates com 5 afastando
do zero. Os comentários explicam as escolhas numéricas onde elas aparecem.

`Decimal` preserva os dígitos textuais, evitando que erros de representação binária
alterem o truncamento. A referência usa pelo menos 50 dígitos, ampliados conforme
as entradas e a precisão pedida. A função `precisao_referencia` cobre as casas
necessárias para soma e produto. Divisões periódicas continuam aproximadas.

As métricas seguem o PDF: `Ea = |referência - aproximado|` e
`Er = Ea / |aproximado|`. Quando o aproximado é zero, o backend devolve `None`
para Er; a interface mostra **Indefinido**, inclusive quando Ea também é zero.

Exemplo de uso do backend, sem abrir uma janela:

```python
from backend.calculos import calcular

resultado = calcular('0.76545', '0.76541', '-', 4, 'arredondar', True)
print(resultado['aproximado'])    # 0.0001000, equivalente a 0.0001
print(resultado['erro_relativo']) # 0.6, equivalente a 60%
```

## Interface

O visual usa uma paleta de azul-marinho, branco e cinza, com azul para as ações
principais. Truncamento é identificado em azul (linha contínua no gráfico) e
arredondamento em violeta (linha tracejada), com legendas para não depender só das
cores. Configuração e resultado aparecem lado a lado em janelas maiores e são
empilhados em janelas menores. A aparência fica em `frontend/estilo.qss`.

- **Calculadora:** quatro operações, ajuste de precisão, métricas, notação
  científica e comparação dos dois métodos sem recalcular o método já escolhido.
- **Somas sucessivas:** entradas configuráveis, gráfico do erro acumulado,
  tabela por etapa, erros finais e exportação CSV.
- **Exemplos do projeto:** carrega os três cenários do enunciado.
- **Como funciona:** explica os conceitos e as entradas.

Entradas aceitam ponto ou vírgula decimal e notação científica (`1e-3`), sem
separadores de milhar. NaN, infinito, divisão por zero e entradas inválidas são
rejeitados. A janela permite até 100 dígitos e 1000 termos; entradas textuais
permitem até 200 caracteres e expoentes de -1000 a 1000. Limites de entrada
protegem a responsividade. Os resultados internos continuam em `Decimal`.
Somente o desenho do gráfico usa floats; magnitudes não representáveis são
indicadas para consulta na tabela. Enter em x ou y calcula; na CLI, Enter vazio
em x ou y volta ao menu.

## Testes

Toda a suíte, com a janela em modo de teste sem abrir no desktop:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Apenas o backend, sem depender da biblioteca visual:

```bash
python3 -m unittest -v tests.test_backend
```

As verificações cobrem os três exemplos, quatro operações, negativos, empates,
transporte de arredondamento, precisão acima de 50 dígitos, casas decimais distantes,
normalização, erro relativo indefinido, entradas inválidas, sequência, interações
na janela, recuperação de erros e exportação CSV.

## Resultados e interpretação do enunciado

| Caso, n = 4 | Referência | Truncamento | Arredondamento |
|---|---:|---:|---:|
| Soma de 0.12345 e 0.67890 | 0.80235 | 0.8023 | 0.8024 |
| 0.76545 - 0.76541, limitando operandos | 0.00004 | 0 | 0.0001 |
| Dez termos de 0.56786, limitando os parciais | 5.6786 | 5.671 | 5.680 |

No cancelamento, truncamento tem Ea = 0.00004 e Er indefinido; arredondamento tem
Ea = 0.00006 e Er = 0.6 (60%). Na sequência, Ea é 0.00760 / 0.00140, respectivamente.

**Inconsistência do PDF:** `1.1357`, `1.7035` e `2.2713` têm cinco dígitos
significativos, embora o exemplo 3 peça quatro. O simulador segue quatro dígitos;
a soma dos dois primeiros termos truncados é `1.135`. São dez termos acumulados
começando em zero. O exemplo de cancelamento limita os operandos; o procedimento
geral limita apenas o resultado. Ambas as opções continuam disponíveis.

O relatório em `docs/` registra a primeira revisão, anterior à reorganização dos
arquivos. Antes da entrega acadêmica, preencha os integrantes e suas contribuições
reais. Publicação no GitHub e participação na apresentação cabem à equipe.
