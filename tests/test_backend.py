"""Resultados esperados do enunciado e regressões da lógica numérica."""
import unittest
from decimal import Decimal as D, getcontext

from backend.calculos import calcular, somar_sequencia, comparar_sequencia
from backend.numeros import ler_decimal, normalizar, ajustar_precisao, calcular_erros


class TestEntradas(unittest.TestCase):
    def test_decimal_com_virgula(self):
        self.assertEqual(ler_decimal(' 0,76545 '), D('0.76545'))

    def test_entradas_invalidas(self):
        for valor in ('', 'NaN', 'inf', '1.000,00', '1e1001', '1e-1001', '1' * 201):
            with self.subTest(valor=valor), self.assertRaises(ValueError):
                ler_decimal(valor)
        with self.assertRaises(ValueError):
            ler_decimal(D('NaN'))

    def test_digitos_preservados(self):
        self.assertEqual(ler_decimal('1.234567890123456789'), D('1.234567890123456789'))

    def test_precisao_invalida(self):
        for n in (0, -1, True, 2.5, '4'):
            with self.subTest(n=n), self.assertRaises(ValueError):
                calcular(1, 2, '+', n, 'truncar')
        with self.assertRaises(ValueError):
            calcular(1, 2, '+', 4, 'outro')

    def test_nomes_completos_dos_metodos(self):
        self.assertEqual(calcular(1, 3, '/', 4, 'truncamento')['modo'], 'truncar')
        self.assertEqual(calcular(1, 3, '/', 4, 'arredondamento')['modo'], 'arredondar')

    def test_quantidade_invalida(self):
        for quantidade in (0, 1001, True, 1.5, '10'):
            with self.subTest(quantidade=quantidade), self.assertRaises(ValueError):
                somar_sequencia(1, quantidade, 4, 'truncar')


class TestPrecisao(unittest.TestCase):
    def test_normalizacao(self):
        for valor in ('0', '10', '-456.78', '0.00123', '1e-1000', '9.999e308'):
            mantissa, expoente = normalizar(D(valor))
            if mantissa != 0:
                self.assertTrue(D('0.1') <= abs(mantissa) < 1)
            # Reconstrução com scaleb, sem potências em float.
            self.assertEqual(mantissa.scaleb(expoente), D(valor))

    def test_negativos_e_empates(self):
        for valor, truncado, arredondado in [
            ('1.2345', '1.234', '1.235'), ('-1.2345', '-1.234', '-1.235'),
            ('0.76545', '0.7654', '0.7655'),
        ]:
            self.assertEqual(ajustar_precisao(valor, 4, 'truncar'), D(truncado))
            self.assertEqual(ajustar_precisao(valor, 4, 'arredondar'), D(arredondado))

    def test_transporte_arredondamento(self):
        resultado = ajustar_precisao('9999.5', 4, 'arredondar')
        self.assertEqual(resultado, D('10000'))
        self.assertEqual(normalizar(resultado), (D('0.1000'), 5))

    def test_truncamento_sem_epsilon(self):
        self.assertEqual(ajustar_precisao('0.67889999999999999', 4, 'truncar'), D('0.6788'))

    def test_idempotencia(self):
        for modo in ('truncar', 'arredondar'):
            for valor in ('0', '1.23', '-0.5678', '6789', '1e-1000', '1e308'):
                primeiro = ajustar_precisao(valor, 4, modo)
                self.assertEqual(ajustar_precisao(primeiro, 4, modo), primeiro)

    def test_metrica_com_denominador_aproximado(self):
        absoluto, relativo = calcular_erros(D(1), D('0.5'))
        self.assertEqual(absoluto, D('0.5'))
        self.assertEqual(relativo, D(1))
        self.assertEqual(calcular_erros(D(-1), D('-0.5')), (D('0.5'), D(1)))

    def test_erro_relativo_indefinido(self):
        self.assertEqual(calcular_erros(D('0.00004'), D(0)), (D('0.00004'), None))
        self.assertEqual(calcular_erros(D(0), D(0)), (D(0), None))


class TestCalculos(unittest.TestCase):
    def test_soma_enunciado(self):
        for modo, esperado in [('truncar', '0.8023'), ('arredondar', '0.8024')]:
            resultado = calcular('0.12345', '0.67890', '+', 4, modo)
            self.assertEqual(resultado['exato'], D('0.80235'))
            self.assertEqual(resultado['aproximado'], D(esperado))
            self.assertEqual(resultado['erro_absoluto'], D('0.00005'))

    def test_cancelamento_arredondado(self):
        resultado = calcular('0.76545', '0.76541', '-', 4, 'arredondar', True)
        for chave, esperado in [('x_aprox', '0.7655'), ('y_aprox', '0.7654'),
                                ('exato', '0.00004'), ('aproximado', '0.0001'),
                                ('erro_absoluto', '0.00006'), ('erro_relativo', '0.6')]:
            self.assertEqual(resultado[chave], D(esperado))

    def test_cancelamento_truncado(self):
        resultado = calcular('0.76545', '0.76541', '-', 4, 'truncar', True)
        self.assertEqual(resultado['aproximado'], 0)
        self.assertEqual(resultado['erro_absoluto'], D('0.00004'))
        self.assertIsNone(resultado['erro_relativo'])

    def test_limitar_apenas_resultado(self):
        resultado = calcular('0.76545', '0.76541', '-', 4, 'truncar')
        self.assertEqual(resultado['aproximado'], D('0.00004'))
        self.assertEqual(resultado['erro_absoluto'], 0)

    def test_operacoes(self):
        for operacao, referencia, truncado, arredondado in [
            ('+', '3.5801', '3.580', '3.580'),
            ('-', '-1.1111', '-1.111', '-1.111'),
            ('*', '2.89564320', '2.895', '2.896'),
        ]:
            for modo, esperado in [('truncar', truncado), ('arredondar', arredondado)]:
                resultado = calcular('1.2345', '2.3456', operacao, 4, modo)
                self.assertEqual(resultado['exato'], D(referencia))
                self.assertEqual(resultado['aproximado'], D(esperado))

    def test_divisao_periodica(self):
        for modo, esperado in [('truncar', '0.6666'), ('arredondar', '0.6667')]:
            resultado = calcular(2, 3, '/', 4, modo)
            self.assertEqual(resultado['aproximado'], D(esperado))
            self.assertGreaterEqual(len(resultado['exato'].as_tuple().digits), 50)

    def test_operacao_invalida_e_divisao_zero(self):
        for operacao, y in [('/', 0), ('%', 1)]:
            with self.assertRaises(ValueError):
                calcular(1, y, operacao, 4, 'truncar')

    def test_referencia_preserva_casas_distantes(self):
        resultado = calcular('1e100', '1e-100', '+', 4, 'truncar')
        self.assertEqual(resultado['erro_absoluto'], D('1e-100'))

    def test_contexto_global_preservado(self):
        precisao_antes = getcontext().prec
        calcular('1e100', '1e-100', '+', 4, 'truncar')
        self.assertEqual(getcontext().prec, precisao_antes)

    def test_precisao_maior_que_50(self):
        resultado = calcular(1, 3, '/', 80, 'arredondar')
        self.assertEqual(len(resultado['aproximado'].as_tuple().digits), 80)

    def test_sequencia_enunciado(self):
        esperados = {
            'truncar': ['0.5678', '1.135', '1.702', '2.269', '2.836', '3.403', '3.970', '4.537', '5.104', '5.671'],
            'arredondar': ['0.5679', '1.136', '1.704', '2.272', '2.840', '3.408', '3.976', '4.544', '5.112', '5.680'],
        }
        for modo, parciais in esperados.items():
            resultado = somar_sequencia('0.56786', 10, 4, modo)
            self.assertEqual([p['aproximado'] for p in resultado['passos']], [D(p) for p in parciais])
            self.assertEqual(resultado['exato'], D('5.6786'))
            esperado = D('0.00760') if modo == 'truncar' else D('0.00140')
            self.assertEqual(resultado['erro_absoluto'], esperado)
            ea, er = calcular_erros(resultado['exato'], resultado['aproximado'])
            self.assertEqual(resultado['erro_relativo'], er)
            self.assertNotEqual(resultado['passos'][1]['erro_local'], resultado['passos'][1]['erro_absoluto'])

    def test_sequencia_generalizada(self):
        resultado = somar_sequencia('0.12345', 3, 3, 'arredondar')
        self.assertEqual(resultado['exato'], D('0.37035'))
        self.assertEqual(len(resultado['passos']), 3)
        self.assertEqual(somar_sequencia('-0.12345', 3, 3, 'truncar')['aproximado'], D('-0.369'))

    def test_comparacao_sequencia(self):
        truncamento, arredondamento = comparar_sequencia('0.56786', 10, 4)
        self.assertEqual(truncamento['modo'], 'truncar')
        self.assertEqual(arredondamento['modo'], 'arredondar')


if __name__ == '__main__':
    unittest.main(verbosity=2)
