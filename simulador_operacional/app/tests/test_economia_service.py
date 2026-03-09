from decimal import Decimal
from django.test import TestCase, override_settings

from ..models import Evento, Grupo, ResultadoFinanceiro
from ..services.economia_service import (
    calcular_custo_total,
    calcular_demanda,
    calcular_preco_final,
)
from ..services.penalidade_service import aplicar_penalidade


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class EconomiaServiceTests(TestCase):
    def setUp(self):
        self.evento_demanda = Evento.objects.create(
            nome="Aumento de Demanda",
            tipo="demanda",
            impacto_percentual=10,
            probabilidade=1,
        )
        self.evento_transporte = Evento.objects.create(
            nome="Custo Transporte",
            tipo="custo_transporte",
            impacto_percentual=20,
            probabilidade=1,
        )

    def test_calcular_custo_total(self):
        custo = calcular_custo_total(10, 100, [self.evento_transporte])
        self.assertEqual(custo, Decimal("120.00"))

    def test_calcular_demanda(self):
        demanda = calcular_demanda(100, Decimal("1.1"), [self.evento_demanda])
        self.assertEqual(demanda, 121)

    def test_calcular_preco_final(self):
        preco = calcular_preco_final(
            Decimal("10"),
            Decimal("2"),
            Decimal("1"),
            [self.evento_demanda],
        )
        self.assertEqual(preco, Decimal("13.20"))


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class PenalidadeServiceTests(TestCase):
    def setUp(self):
        self.grupo = Grupo.objects.create(nome="G1", capital=Decimal("100"))

    def test_aplicar_penalidade(self):
        aplicar_penalidade(self.grupo, 1, Decimal("10"))
        self.grupo.refresh_from_db()
        self.assertEqual(self.grupo.capital, Decimal("90"))
        rf = ResultadoFinanceiro.objects.get(grupo=self.grupo, rodada=1)
        self.assertEqual(rf.penalidades, Decimal("10"))
        self.assertEqual(rf.custos, Decimal("10"))
