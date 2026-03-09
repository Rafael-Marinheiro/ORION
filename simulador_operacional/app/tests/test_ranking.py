from decimal import Decimal

from django.test import TestCase, override_settings

from app.models import Cidade, Distribuicao, Grupo, ResultadoFinanceiro
from app.services.classificacao import calcular_ranking


@override_settings(MIGRATION_MODULES={"app": None})
class RankingServiceTest(TestCase):
    def test_ranking_prioritizes_operational_efficiency(self):
        cidade = Cidade.objects.create(nome="X", distancia_km=10, demanda=100)
        g1 = Grupo.objects.create(nome="G1", capital=1000)
        g2 = Grupo.objects.create(nome="G2", capital=1000)

        Distribuicao.objects.create(
            grupo=g1,
            cidade=cidade,
            rodada=1,
            quantidade=60,
            preco_unitario=10,
            custo_transporte=0,
            quantidade_vendida=50,
        )
        Distribuicao.objects.create(
            grupo=g2,
            cidade=cidade,
            rodada=1,
            quantidade=100,
            preco_unitario=10,
            custo_transporte=0,
            quantidade_vendida=50,
        )

        ResultadoFinanceiro.objects.create(
            grupo=g1,
            rodada=1,
            lucro=Decimal("200"),
            saldo_caixa=Decimal("1000"),
            penalidades=Decimal("0"),
        )
        ResultadoFinanceiro.objects.create(
            grupo=g2,
            rodada=1,
            lucro=Decimal("200"),
            saldo_caixa=Decimal("1000"),
            penalidades=Decimal("0"),
        )

        ranking = calcular_ranking()
        self.assertEqual([g.nome for g in ranking], ["G1", "G2"])

    def test_ranking_resolves_tie_with_cash_balance(self):
        cidade = Cidade.objects.create(nome="X", distancia_km=10, demanda=100)
        g1 = Grupo.objects.create(nome="G1", capital=1000)
        g2 = Grupo.objects.create(nome="G2", capital=1000)

        for rodada in [1, 2]:
            Distribuicao.objects.create(
                grupo=g1,
                cidade=cidade,
                rodada=rodada,
                quantidade=50,
                preco_unitario=10,
                custo_transporte=0,
                quantidade_vendida=50,
            )
            Distribuicao.objects.create(
                grupo=g2,
                cidade=cidade,
                rodada=rodada,
                quantidade=50,
                preco_unitario=10,
                custo_transporte=0,
                quantidade_vendida=50,
            )

        ResultadoFinanceiro.objects.create(
            grupo=g1,
            rodada=2,
            lucro=Decimal("200"),
            saldo_caixa=Decimal("1000"),
            penalidades=Decimal("0"),
        )
        ResultadoFinanceiro.objects.create(
            grupo=g2,
            rodada=2,
            lucro=Decimal("200"),
            saldo_caixa=Decimal("800"),
            penalidades=Decimal("0"),
        )

        ranking = calcular_ranking()
        self.assertEqual([g.nome for g in ranking], ["G1", "G2"])

    def test_ranking_resolves_tie_with_penalties(self):
        cidade = Cidade.objects.create(nome="X", distancia_km=10, demanda=100)
        g1 = Grupo.objects.create(nome="G1", capital=1000)
        g2 = Grupo.objects.create(nome="G2", capital=1000)

        for rodada in [1, 2]:
            Distribuicao.objects.create(
                grupo=g1,
                cidade=cidade,
                rodada=rodada,
                quantidade=50,
                preco_unitario=10,
                custo_transporte=0,
                quantidade_vendida=50,
            )
            Distribuicao.objects.create(
                grupo=g2,
                cidade=cidade,
                rodada=rodada,
                quantidade=50,
                preco_unitario=10,
                custo_transporte=0,
                quantidade_vendida=50,
            )

        ResultadoFinanceiro.objects.create(
            grupo=g1,
            rodada=2,
            lucro=Decimal("200"),
            saldo_caixa=Decimal("1000"),
            penalidades=Decimal("10"),
        )
        ResultadoFinanceiro.objects.create(
            grupo=g2,
            rodada=2,
            lucro=Decimal("200"),
            saldo_caixa=Decimal("1000"),
            penalidades=Decimal("20"),
        )

        ranking = calcular_ranking()
        self.assertEqual([g.nome for g in ranking], ["G1", "G2"])
