"""Integração dos formulários com Qt e com o núcleo decimal (sem display)."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import csv
import tempfile
import subprocess
import sys
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from frontend.janela import JanelaSimulador


class TestJanela(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.janela = JanelaSimulador()
        self.janela.show()
        self.app.processEvents()

    def tearDown(self):
        self.janela.close()
        self.janela.deleteLater()
        self.app.processEvents()

    def test_calcular_por_botao(self):
        QTest.mouseClick(self.janela.calcular_botao, Qt.LeftButton)
        self.assertEqual(self.janela.ultimo_resultado['aproximado'], Decimal('0.0001'))
        self.assertIn('60.00%', self.janela.metricas.item(2, 1).text())

    def test_comparacao_cancelamento(self):
        self.janela.comparar()
        self.assertFalse(self.janela.comparacao.isHidden())
        self.assertIn('Indefinido', self.janela.comparacao.item(0, 3).text())
        self.assertIn('60.00%', self.janela.comparacao.item(1, 3).text())

    def test_comparacao_calcula_cada_metodo_uma_vez(self):
        from backend.calculos import calcular
        with patch('frontend.janela.calcular', wraps=calcular) as operacao:
            self.janela.comparar()
        self.assertEqual(operacao.call_count, 2)

    def test_entrada_invalida_limpa_resultado_anterior(self):
        self.janela.calcular()
        self.janela.x.setText('abc')
        self.janela.calcular()
        self.assertIsNone(self.janela.ultimo_resultado)
        self.assertEqual(self.janela.metricas.rowCount(), 0)
        self.assertFalse(self.janela.erro.isHidden())

    def test_divisao_zero_sem_fechar(self):
        self.janela.y.setText('0')
        self.janela.operacao.setCurrentIndex(3)
        self.janela.calcular()
        self.assertFalse(self.janela.erro.isHidden())
        self.assertIn('zero', self.janela.erro.text())
        self.janela.y.setText('2')
        self.janela.calcular()
        self.assertTrue(self.janela.erro.isHidden())

    def test_limpar(self):
        self.janela.calcular()
        self.janela.limpar()
        self.assertEqual(self.janela.x.text(), '')
        self.assertEqual(self.janela.metricas.rowCount(), 0)
        self.assertIsNone(self.janela.ultimo_resultado)

    def test_exemplos(self):
        self.janela.carregar_exemplo(0)
        self.assertEqual(self.janela.ultimo_resultado['aproximado'], Decimal('0.8024'))
        self.janela.carregar_exemplo(1)
        self.assertEqual(self.janela.ultimo_resultado['erro_relativo'], Decimal('0.6'))
        self.janela.carregar_exemplo(2)
        self.assertEqual(self.janela.paginas.currentIndex(), 1)
        self.assertEqual(self.janela.tabela_sequencia.rowCount(), 10)

    def test_sequencia_por_botao(self):
        self.janela.navegar(1)
        QTest.mouseClick(self.janela.simular_botao, Qt.LeftButton)
        self.assertEqual(self.janela.tabela_sequencia.item(9, 2).text(), '5.671')
        self.assertTrue(self.janela.exportar.isEnabled())

    def test_sequencia_invalida(self):
        self.janela.termo.setText('abc')
        self.janela.simular()
        self.assertFalse(self.janela.erro_sequencia.isHidden())
        self.assertFalse(self.janela.exportar.isEnabled())

    def test_sequencia_invalida_impede_exportar_dados_antigos(self):
        self.janela.simular()
        self.janela.termo.setText('abc')
        self.janela.simular()
        self.assertIsNone(self.janela.ultima_sequencia)
        self.assertFalse(self.janela.exportar.isEnabled())
        self.assertEqual(self.janela.tabela_sequencia.rowCount(), 0)

    def test_exportacao_csv(self):
        self.janela.simular()
        with tempfile.TemporaryDirectory() as pasta:
            destino = str(Path(pasta) / 'dados.csv')
            with patch('frontend.janela.QFileDialog.getSaveFileName', return_value=(destino, 'CSV')):
                self.janela.exportar_csv()
            with open(destino, encoding='utf-8-sig') as arquivo:
                linhas = list(csv.reader(arquivo, delimiter=';'))
            self.assertEqual(len(linhas), 11)
            self.assertEqual(linhas[-1][2], '5.671')
            self.assertEqual(linhas[-1][5], '5.680')

    def test_exportacao_cancelada(self):
        self.janela.simular()
        with patch('frontend.janela.QFileDialog.getSaveFileName', return_value=('', '')):
            self.janela.exportar_csv()

    def test_grafico_extremos(self):
        for valor in ('1e-1000', '1e1000', '0'):
            self.janela.termo.setText(valor)
            self.janela.simular()
            self.janela.grafico.grab()
            self.assertTrue(self.janela.erro_sequencia.isHidden())


class TestTerminal(unittest.TestCase):
    def test_duas_operacoes_e_saida(self):
        main = Path(__file__).resolve().parents[1] / 'main.py'
        entradas = '1\n1\n2\n+\n4\nt\nn\n1\n3\n4\n*\n4\na\nn\n3\n'
        processo = subprocess.run([sys.executable, str(main), '--cli'],
                                  input=entradas, text=True, capture_output=True, timeout=10)
        self.assertEqual(processo.returncode, 0)
        self.assertEqual(processo.stdout.count('Referência:'), 2)
        self.assertIn('Aproximado: 12', processo.stdout)

    def test_exemplos_sem_importar_qt(self):
        # Esta apresentação deve funcionar mesmo sem a dependência gráfica.
        script = 'import sys; from frontend.terminal import demonstrar_exemplos; demonstrar_exemplos(); assert "PySide6" not in sys.modules'
        processo = subprocess.run([sys.executable, '-c', script],
                                  text=True, capture_output=True, timeout=10)
        self.assertEqual(processo.returncode, 0, processo.stderr)
        self.assertIn('60.00%', processo.stdout)


if __name__ == '__main__':
    unittest.main(verbosity=2)
