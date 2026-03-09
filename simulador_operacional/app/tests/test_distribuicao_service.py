from decimal import Decimal

from django.test import TestCase, override_settings

from ..models import Cidade, Distribuicao, Grupo
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
        )
        Distribuicao.objects.create(
            grupo=self.g2,
            cidade=self.cidade,
            rodada=1,
            quantidade=50,
            preco_unitario=Decimal("8"),
            custo_transporte=0,
        )

        distribuir_demanda(1)

        envio1 = Distribuicao.objects.get(grupo=self.g1)
        envio2 = Distribuicao.objects.get(grupo=self.g2)
        self.assertEqual(envio2.quantidade_vendida, 50)
        self.assertEqual(envio1.quantidade_vendida, 50)
        self.assertEqual(envio1.quantidade_sobra, 30)

    def test_limite_demanda_prioriza_menor_preco(self):
        self.cidade.limite_demanda = 60
        self.cidade.save(update_fields=["limite_demanda"])

        Distribuicao.objects.create(
            grupo=self.g1,
            cidade=self.cidade,
            rodada=1,
            quantidade=40,
            preco_unitario=Decimal("9"),
            custo_transporte=0,
        )
        Distribuicao.objects.create(
            grupo=self.g2,
            cidade=self.cidade,
            rodada=1,
            quantidade=40,
            preco_unitario=Decimal("10"),
            custo_transporte=0,
        )

        distribuir_demanda(1)

        envio1 = Distribuicao.objects.get(grupo=self.g1)
        envio2 = Distribuicao.objects.get(grupo=self.g2)
        self.assertEqual(envio1.quantidade_vendida, 40)
        self.assertEqual(envio2.quantidade_vendida, 20)
        self.assertEqual(envio2.quantidade_sobra, 20)
