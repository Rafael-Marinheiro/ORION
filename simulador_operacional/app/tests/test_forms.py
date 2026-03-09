from django.test import TestCase, override_settings

from app.forms import ConfigWizardStep1Form, InvestimentoForm, GameConfigForm
from app.models import Cidade, GameConfig, Produto


@override_settings(MIGRATION_MODULES={"app": None})
class GameConfigFormTest(TestCase):
    def test_save_ranking_weights_when_sum_is_one(self):
        config = GameConfig.objects.create()
        form = GameConfigForm(
            data={
                "capital_inicial": "1000",
                "estoque_inicial": 0,
                "maquinas_iniciais": 1,
                "maquinas_iniciais_a": 1,
                "maquinas_iniciais_b": 1,
                "maquinas_iniciais_c": 1,
                "trabalhadores_iniciais": 2,
                "capacidade_maquina": 100,
                "numero_rodadas": 3,
                "produtos_habilitados": "A,B,C",
                "modulo_producao": True,
                "modulo_distribuicao": True,
                "modulo_financeiro": True,
                "regra_eventos": "{}",
                "peso_lucro": "0.5",
                "peso_market_share": "0.2",
                "peso_atendimento": "0.2",
                "peso_eficiencia_estoque": "0.1",
            },
            instance=config,
        )

        self.assertTrue(form.is_valid(), form.errors)
        salvo = form.save()
        self.assertEqual(salvo.ranking_pesos["lucro"], 0.5)
        self.assertEqual(salvo.ranking_pesos["market_share"], 0.2)
        self.assertEqual(salvo.ranking_pesos["atendimento"], 0.2)
        self.assertEqual(salvo.ranking_pesos["eficiencia_estoque"], 0.1)

    def test_invalid_when_weights_sum_is_not_one(self):
        config = GameConfig.objects.create()
        form = GameConfigForm(
            data={
                "capital_inicial": "1000",
                "estoque_inicial": 0,
                "maquinas_iniciais": 1,
                "maquinas_iniciais_a": 1,
                "maquinas_iniciais_b": 1,
                "maquinas_iniciais_c": 1,
                "trabalhadores_iniciais": 2,
                "capacidade_maquina": 100,
                "numero_rodadas": 3,
                "produtos_habilitados": "A,B,C",
                "modulo_producao": True,
                "modulo_distribuicao": True,
                "modulo_financeiro": True,
                "regra_eventos": "{}",
                "peso_lucro": "0.5",
                "peso_market_share": "0.2",
                "peso_atendimento": "0.2",
                "peso_eficiencia_estoque": "0.2",
            },
            instance=config,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("A soma dos pesos deve ser igual a 1.0.", form.non_field_errors())


@override_settings(MIGRATION_MODULES={"app": None})
class InvestimentoFormTest(TestCase):
    def setUp(self):
        self.cidade = Cidade.objects.create(nome="Cidade X", distancia_km=100, demanda=1000)
        self.produto = Produto.objects.create(codigo="AX", nome="Produto AX", ativo=True)

    def test_marketing_exige_cidade(self):
        form = InvestimentoForm(
            data={
                "categoria": "marketing",
                "quantidade": 1,
                "valor": "1000",
                "operacao_financeira": "aplicar",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("cidade", form.errors)

    def test_maquinas_exige_produto(self):
        form = InvestimentoForm(
            data={
                "categoria": "maquinas",
                "cidade": self.cidade.id,
                "quantidade": 1,
                "valor": "1000",
                "operacao_financeira": "aplicar",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("produto", form.errors)

    def test_financeiro_permite_aplicar_resgatar(self):
        form = InvestimentoForm(
            data={
                "categoria": "financeiro",
                "quantidade": 1,
                "valor": "1000",
                "operacao_financeira": "resgatar",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)


@override_settings(MIGRATION_MODULES={"app": None})
class ConfigWizardStep1FormTest(TestCase):
    def test_valida_campos_base(self):
        form = ConfigWizardStep1Form(
            data={
                "capital_inicial": "100000",
                "estoque_inicial": 0,
                "maquinas_iniciais": 5,
                "capacidade_maquina": 100,
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
