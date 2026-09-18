"""Fixa os parametros economicos que a especificacao define por extenso.

Estes valores mudam o equilibrio do jogo inteiro, entao ficam presos a um
teste que cita a origem documental. Quem mudar um numero aqui esta mudando
uma regra de negocio, nao um detalhe.
"""

import tempfile
from decimal import Decimal
from pathlib import Path

from django.test import TestCase
from django.utils import timezone

from app.models import Grupo, ResultadoFinanceiro, Rodada
from app.parametros import (
    CUSTO_OPERADOR_POR_RODADA,
    OPERADORES_POR_MAQUINA,
    PERCENTUAL_PENALIDADE_SEM_SUBMISSAO,
    SALARIO_OPERADOR_MENSAL,
    TAXA_APLICACAO_FINANCEIRA_RODADA,
)
from app.services.fechamento import fechar_rodada


class ParametrosDaEspecificacaoTest(TestCase):
    def test_salario_do_operador_e_o_do_documento(self):
        # 14.2.4: "Salario por funcionario: R$ 1.800,00/mes"
        self.assertEqual(SALARIO_OPERADOR_MENSAL, Decimal("1800"))

    def test_a_rodada_fecha_uma_folha_sem_converter_por_tempo(self):
        """A rodada e o periodo de competencia, nao um numero de semanas.

        O professor define a data de encerramento livremente, entao converter
        o salario por tempo decorrido faria o custo da mesma decisao mudar
        conforme o prazo da rodada.
        """
        self.assertEqual(CUSTO_OPERADOR_POR_RODADA, SALARIO_OPERADOR_MENSAL)
        # o valor anterior, R$ 2.000, nao vinha de documento nenhum
        self.assertNotEqual(CUSTO_OPERADOR_POR_RODADA, Decimal("2000"))

    def test_demais_parametros(self):
        self.assertEqual(TAXA_APLICACAO_FINANCEIRA_RODADA, Decimal("0.015"))  # 14.4.1
        self.assertEqual(PERCENTUAL_PENALIDADE_SEM_SUBMISSAO, Decimal("0.10"))  # 11.2
        self.assertEqual(OPERADORES_POR_MAQUINA, 2)  # 14.3


class BaseDaPenalidadeTest(TestCase):
    """11.2: a multa incide sobre o caixa ao final da rodada ANTERIOR."""

    def setUp(self):
        self.grupo = Grupo.objects.create(nome="Equipe Vega", capital=Decimal("100000"))

    def test_usa_o_caixa_da_rodada_anterior_e_nao_o_capital(self):
        # caixa da rodada 1 bem diferente do capital, para os dois nao se
        # confundirem no resultado
        ResultadoFinanceiro.objects.create(
            grupo=self.grupo, rodada=1, saldo_caixa=Decimal("20000")
        )
        Rodada.objects.create(numero=2, fim=timezone.now())

        with tempfile.TemporaryDirectory() as tmp:
            fechar_rodada(2, pasta_relatorios=Path(tmp))

        rf = ResultadoFinanceiro.objects.get(grupo=self.grupo, rodada=2)
        # 10% de 20.000 (caixa da rodada 1), nao de 100.000 (capital)
        self.assertEqual(rf.penalidades, Decimal("2000"))

    def test_primeira_rodada_cai_no_capital_por_nao_haver_anterior(self):
        Rodada.objects.create(numero=1, fim=timezone.now())

        with tempfile.TemporaryDirectory() as tmp:
            fechar_rodada(1, pasta_relatorios=Path(tmp))

        rf = ResultadoFinanceiro.objects.get(grupo=self.grupo, rodada=1)
        self.assertEqual(rf.penalidades, Decimal("10000"))
