from decimal import Decimal

from django.test import TestCase, override_settings

from ..models import Cidade, Distribuicao, Grupo, VendaCidade
from ..services.distribuicao_service import distribuir_demanda


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class DistribuicaoServiceTest(TestCase):
    def setUp(self):
        self.cidade = Cidade.objects.create(nome="Cidade", distancia_km=10, demanda=100)
        self.g1 = Grupo.objects.create(nome="G1")
        self.g2 = Grupo.objects.create(nome="G2")

    def test_preco_influencia_vendas(self):
        Distribuicao.objects.create(
            grupo=self.g1,
            cidade=self.cidade,
            rodada=1,
            quantidade=80,
            preco_unitario=Decimal("10"),
            custo_transporte=0,
            fator_marketing=Decimal("1"),
        )
        Distribuicao.objects.create(
            grupo=self.g2,
            cidade=self.cidade,
            rodada=1,
            quantidade=50,
            preco_unitario=Decimal("8"),
            custo_transporte=0,
            fator_marketing=Decimal("1"),
        )

        distribuir_demanda(1)

        envio1 = Distribuicao.objects.get(grupo=self.g1)
        envio2 = Distribuicao.objects.get(grupo=self.g2)
        self.assertEqual(envio2.vendas_realizadas, 50)
        self.assertEqual(envio1.vendas_realizadas, 50)

        venda1 = VendaCidade.objects.get(grupo=self.g1, cidade=self.cidade, rodada=1)
        venda2 = VendaCidade.objects.get(grupo=self.g2, cidade=self.cidade, rodada=1)
        self.assertEqual(venda2.quantidade_vendida, 50)
        self.assertEqual(venda1.quantidade_vendida, 50)

    def test_marketing_supera_preco(self):
        Distribuicao.objects.create(
            grupo=self.g1,
            cidade=self.cidade,
            rodada=1,
            quantidade=70,
            preco_unitario=Decimal("10"),
            custo_transporte=0,
            fator_marketing=Decimal("1.50"),
        )
        Distribuicao.objects.create(
            grupo=self.g2,
            cidade=self.cidade,
            rodada=1,
            quantidade=70,
            preco_unitario=Decimal("8"),
            custo_transporte=0,
            fator_marketing=Decimal("1"),
        )

        distribuir_demanda(1)

        envio1 = Distribuicao.objects.get(grupo=self.g1)
        envio2 = Distribuicao.objects.get(grupo=self.g2)
        self.assertEqual(envio1.vendas_realizadas, 70)
        self.assertEqual(envio2.vendas_realizadas, 30)
