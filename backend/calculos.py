"""Fluxo principal: operações, simulação da máquina e propagação de erros."""
from decimal import Decimal, localcontext
from backend.numeros import (
    ler_decimal, precisao_referencia, validar_configuracao,
    normalizar, ajustar_precisao, calcular_erros,
)


def operar(x, y, operacao, n_digitos=4):
    """As quatro operações em precisão de referência, sem limitar o resultado."""
    with localcontext() as contexto:
        contexto.prec = precisao_referencia(x, y, minimo=max(50, n_digitos + 10))
        if operacao == '+':
            return x + y
        if operacao == '-':
            return x - y
        if operacao == '*':
            return x * y
        if operacao == '/':
            if y == 0:
                raise ValueError('Divisão por zero não permitida.')
            return x / y
        raise ValueError('Operação inválida. Use +, -, * ou /.')


def calcular(x, y, operacao, n_digitos, modo, limitar_operandos=False):
    """Uma operação completa em cinco etapas, com um dicionário de resultados."""
    # 1. Valida as escolhas e converte as entradas para Decimal.
    modo = validar_configuracao(n_digitos, modo)
    x = ler_decimal(x)
    y = ler_decimal(y)

    # 2. Calcula a referência usando os números originais.
    referencia = operar(x, y, operacao, n_digitos)

    # 3. Opcionalmente simula como a máquina armazena os operandos.
    x_aproximado = x
    y_aproximado = y
    if limitar_operandos:
        x_aproximado = ajustar_precisao(x, n_digitos, modo)
        y_aproximado = ajustar_precisao(y, n_digitos, modo)
        resultado = operar(x_aproximado, y_aproximado, operacao, n_digitos)
    else:
        resultado = referencia

    # 4. Limita o resultado e compara com a referência.
    aproximado = ajustar_precisao(resultado, n_digitos, modo)
    erro_absoluto, erro_relativo = calcular_erros(referencia, aproximado)

    # 5. Devolve os dados. A interface decide como mostrá-los.
    return {
        'x': x,
        'y': y,
        'operacao': operacao,
        'x_aprox': x_aproximado,
        'y_aprox': y_aproximado,
        'exato': referencia,
        'aproximado': aproximado,
        'cientifico_exato': normalizar(referencia),
        'cientifico_aproximado': normalizar(aproximado),
        'erro_absoluto': erro_absoluto,
        'erro_relativo': erro_relativo,
        'n_digitos': n_digitos,
        'modo': modo,
        'limitar_operandos': limitar_operandos,
    }


def somar_sequencia(valor, quantidade, n_digitos, modo, limitar_operandos=False):
    """Soma o mesmo termo repetidamente, limitando cada resultado parcial."""
    modo = validar_configuracao(n_digitos, modo)
    if isinstance(quantidade, bool) or not isinstance(quantidade, int) or not 1 <= quantidade <= 1000:
        raise ValueError('Use entre 1 e 1000 termos inteiros.')
    valor = ler_decimal(valor)
    acumulado = Decimal(0)
    passos = []

    for indice in range(1, quantidade + 1):
        resultado = calcular(acumulado, valor, '+', n_digitos, modo, limitar_operandos)
        acumulado = resultado['aproximado']

        # A referência ideal é independente das aproximações das somas anteriores.
        referencia = operar(valor, Decimal(indice), '*', n_digitos)
        erro_absoluto, erro_relativo = calcular_erros(referencia, acumulado)
        passos.append({
            'indice': indice,
            'exato': referencia,
            'aproximado': acumulado,
            'erro_local': resultado['erro_absoluto'],
            'erro_absoluto': erro_absoluto,
            'erro_relativo': erro_relativo,
        })

    # Reutiliza o último passo para o resumo, sem recalcular as métricas finais.
    resumo = passos[-1].copy()
    resumo['passos'] = passos
    resumo['modo'] = modo
    return resumo


def comparar_sequencia(valor, quantidade, n_digitos, limitar_operandos=False):
    """Executa a mesma sequência uma vez com cada método."""
    truncamento = somar_sequencia(valor, quantidade, n_digitos, 'truncar', limitar_operandos)
    arredondamento = somar_sequencia(valor, quantidade, n_digitos, 'arredondar', limitar_operandos)
    return truncamento, arredondamento
