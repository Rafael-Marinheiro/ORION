from decimal import Decimal

from django.test import TestCase, override_settings

from app.models import Cidade, Grupo, Investimento, LinhaProducao
from app.services.investimentos import aplicar_retorno_investimentos
from app.services.producao import calcular_eficiencia, registrar_producao
from app.services.vendas import calcular_demanda


@override_settings(MIGRATION_MODULES={"app": None})
class ServicosBasicosTest(TestCase):
    def test_producao_registro_e_eficiencia(self):
        grupo = Grupo.objects.create(nome="G1")
        linha = LinhaProducao.objects.create(grupo=grupo, capacidade=100, producao=0)

        registrar_producao(linha, 40)
        linha.refresh_from_db()

        self.assertEqual(linha.producao, 40)
        self.assertEqual(calcular_eficiencia(linha), 0.4)

    def test_calcular_demanda_respeita_limite_e_disponibilidade(self):
        cidade = Cidade.objects.create(nome="Cidade X", distancia_km=100, demanda=100, limite_demanda=30)
        demanda = calcular_demanda(
            cidade=cidade,
            preco=Decimal("2"),
            fator_marketing=Decimal("2"),
            disponibilidade=50,
        )
        self.assertEqual(demanda, 30)

    def test_aplicar_retorno_investimentos(self):
        grupo = Grupo.objects.create(nome="G2", capital=Decimal("1000"))
        investimento = Investimento.objects.create(
            grupo=grupo,
            categoria="maquinas",
            valor=Decimal("1000"),
            rodada=1,
        )
        investimento.tempo_maturacao = 1
        investimento.roi = Decimal("0.10")
        investimento.save(update_fields=["tempo_maturacao", "roi"])

        aplicar_retorno_investimentos(grupo, rodada_atual=2)
        grupo.refresh_from_db()
        investimento.refresh_from_db()

        self.assertEqual(grupo.capital, Decimal("1100"))
        self.assertTrue(investimento.retorno_aplicado)
