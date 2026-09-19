"""Fator de marketing do 14.1.1.

A curva anterior era linear e praticamente inerte: R$ 10.000 -- o teto do
documento -- rendiam 1,02, dois por cento de demanda a mais. Com a curva
logaritmica o mesmo valor rende os 20% que o documento promete.
"""

from decimal import Decimal

from django.test import TestCase

from app.models import Cidade, Grupo, Investimento
from app.parametros import GANHO_MAXIMO_MARKETING, INVESTIMENTO_MARKETING_TETO
from app.services.marketing import fator_de_investimento, fator_marketing


class CurvaDoMarketingTest(TestCase):
    def test_sem_investimento_nao_altera_a_demanda(self):
        self.assertEqual(fator_de_investimento(0), Decimal("1"))

    def test_no_teto_entrega_o_ganho_maximo(self):
        """14.1.1: "limite de aumento de ate 20% da demanda base"."""
        self.assertEqual(
            fator_de_investimento(INVESTIMENTO_MARKETING_TETO),
            Decimal("1") + GANHO_MAXIMO_MARKETING,
        )

    def test_acima_do_teto_nao_ganha_nada_a_mais(self):
        """"Investimentos superiores a R$ 10.000,00 nao geram aumento adicional"."""
        self.assertEqual(
            fator_de_investimento(Decimal("50000")),
            fator_de_investimento(INVESTIMENTO_MARKETING_TETO),
        )

    def test_curva_e_crescente(self):
        valores = [Decimal(v) for v in ("500", "1000", "2500", "5000", "10000")]
        fatores = [fator_de_investimento(v) for v in valores]

        self.assertEqual(fatores, sorted(fatores))

    def test_retorno_marginal_decrescente(self):
        """Os primeiros mil reais rendem mais que os ultimos nove mil."""
        primeiro_ganho = fator_de_investimento(1000) - fator_de_investimento(0)
        resto = fator_de_investimento(10000) - fator_de_investimento(1000)

        self.assertGreater(primeiro_ganho, resto)

    def test_valor_do_documento(self):
        # 1 + 0,20 x ln(1001)/ln(10001) = 1 + 0,20 x 0,7501
        self.assertEqual(fator_de_investimento(1000), Decimal("1.1500"))


class FatorPorCidadeTest(TestCase):
    def setUp(self):
        self.grupo = Grupo.objects.create(nome="Equipe Vega", capital=Decimal("100000"))
        self.cidade = Cidade.objects.create(nome="Caico", distancia_km=100, demanda=200)
        self.outra = Cidade.objects.create(nome="Natal", distancia_km=172, demanda=1550)

    def test_campanha_vale_so_na_cidade_em_que_foi_feita(self):
        """14.1: "investimentos em marketing por cidade"."""
        Investimento.objects.create(
            grupo=self.grupo,
            rodada=1,
            categoria="marketing",
            cidade=self.cidade,
            valor=Decimal("5000"),
            rodada_ativacao=1,
        )

        self.assertGreater(fator_marketing(self.grupo, self.cidade, 1), Decimal("1"))
        self.assertEqual(fator_marketing(self.grupo, self.outra, 1), Decimal("1"))

    def test_campanha_futura_ainda_nao_conta(self):
        Investimento.objects.create(
            grupo=self.grupo,
            rodada=1,
            categoria="marketing",
            cidade=self.cidade,
            valor=Decimal("5000"),
            rodada_ativacao=3,
        )

        self.assertEqual(fator_marketing(self.grupo, self.cidade, 2), Decimal("1"))
        self.assertGreater(fator_marketing(self.grupo, self.cidade, 3), Decimal("1"))

    def test_campanhas_se_acumulam_ate_o_teto(self):
        for _ in range(2):
            Investimento.objects.create(
                grupo=self.grupo,
                rodada=1,
                categoria="marketing",
                cidade=self.cidade,
                valor=Decimal("6000"),
                rodada_ativacao=1,
            )

        self.assertEqual(
            fator_marketing(self.grupo, self.cidade, 1),
            Decimal("1") + GANHO_MAXIMO_MARKETING,
        )
