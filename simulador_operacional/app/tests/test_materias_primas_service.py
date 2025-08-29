from decimal import Decimal
from django.test import TestCase, override_settings

from ..services.materias_primas import (
    calcular_frete,
    calcular_armazenagem,
    calcular_custo_logistico,
)


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class MateriasPrimasServiceTest(TestCase):
    def test_calcular_frete_sem_desconto(self):
        self.assertEqual(calcular_frete(100), Decimal("150.00"))

    def test_calcular_frete_com_desconto(self):
        self.assertEqual(
            calcular_frete(100, remessa_simultanea=True), Decimal("100.00")
        )

    def test_calcular_armazenagem(self):
        self.assertEqual(
            calcular_armazenagem(Decimal("1000"), 2), Decimal("40.00")
        )

    def test_calcular_custo_logistico(self):
        custo = calcular_custo_logistico(50, Decimal("500"))
        self.assertEqual(custo, Decimal("85.00"))
