"""Conversão, precisão significativa e métricas de erro."""
from decimal import Decimal, InvalidOperation, localcontext, ROUND_DOWN, ROUND_HALF_UP


def ler_decimal(valor):
    """Converte a entrada preservando os dígitos escritos pelo usuário."""
    if isinstance(valor, Decimal):
        numero = valor
    else:
        texto = str(valor).strip().replace(',', '.')
        if not texto:
            raise ValueError('Preencha os valores antes de calcular.')
        if len(texto) > 200:
            raise ValueError('Use no máximo 200 caracteres por número.')
        try:
            numero = Decimal(texto)
        except InvalidOperation:
            raise ValueError('Digite um número decimal válido.') from None
        # O limite vale para entradas. Resultados internos podem ter outra magnitude.
        if numero.is_finite() and (
            abs(numero.adjusted()) > 1000 or abs(numero.as_tuple().exponent) > 1000
        ):
            raise ValueError('Use expoentes entre -1000 e 1000.')
    if not numero.is_finite():
        raise ValueError('O número deve ser finito: NaN e infinito não são aceitos.')
    return numero


def precisao_referencia(*valores, minimo=50):
    """Escolhe quantos dígitos o Decimal precisa para o cálculo de referência.

    A soma precisa cobrir a distância entre a maior e a menor casa decimal.
    O produto pode ter tantos dígitos quanto os dois coeficientes juntos.
    Divisões periódicas usam pelo menos 50 dígitos, mas continuam aproximadas.
    """
    digitos_produto = sum(len(valor.as_tuple().digits) for valor in valores)
    maior_casa = max(valor.adjusted() for valor in valores)
    menor_casa = min(valor.as_tuple().exponent for valor in valores)
    return max(minimo, digitos_produto + 10, maior_casa - menor_casa + 10)


def validar_configuracao(n_digitos, modo):
    if isinstance(n_digitos, bool) or not isinstance(n_digitos, int) or n_digitos < 1:
        raise ValueError('O número de dígitos deve ser um inteiro positivo.')
    if modo == 'truncamento':
        modo = 'truncar'
    elif modo == 'arredondamento':
        modo = 'arredondar'
    if modo not in ('truncar', 'arredondar'):
        raise ValueError('O método deve ser truncar ou arredondar.')
    return modo


def normalizar(valor):
    """Exemplo: 123.45 = 0.12345 × 10³. Zero retorna (0, 0)."""
    if valor == 0:
        return valor, 0
    expoente = valor.adjusted() + 1
    with localcontext() as contexto:
        contexto.prec = precisao_referencia(valor)
        mantissa = valor.scaleb(-expoente)
    return mantissa, expoente


def ajustar_precisao(valor, n_digitos, modo):
    """Normaliza → limita a mantissa → reconstrói o número decimal."""
    modo = validar_configuracao(n_digitos, modo)
    valor = ler_decimal(valor)
    mantissa, expoente = normalizar(valor)
    with localcontext() as contexto:
        contexto.prec = max(n_digitos + 10, len(mantissa.as_tuple().digits) + 10)
        # Na mantissa 0.12345, n=4 corresponde à unidade 0.0001.
        unidade = Decimal(1).scaleb(-n_digitos)
        if modo == 'truncar':
            regra = ROUND_DOWN       # Corta em direção ao zero, mesmo em negativos.
        else:
            regra = ROUND_HALF_UP    # Empates com 5 são afastados do zero.
        mantissa = mantissa.quantize(unidade, rounding=regra)
        return mantissa.scaleb(expoente)


def calcular_erros(referencia, aproximado):
    """Retorna (Ea, Er). Er é None se o denominador aproximado for zero."""
    with localcontext() as contexto:
        contexto.prec = precisao_referencia(referencia, aproximado)
        erro_absoluto = abs(referencia - aproximado)
        if aproximado == 0:
            erro_relativo = None
        else:
            erro_relativo = erro_absoluto / abs(aproximado)
    return erro_absoluto, erro_relativo
