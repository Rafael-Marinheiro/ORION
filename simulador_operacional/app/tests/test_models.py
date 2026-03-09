from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from app.models import (
    CapacidadeProdutoGrupo,
    ComposicaoProduto,
    GameConfig,
    Grupo,
    Investimento,
    Jogo,
    MateriaPrima,
    Produto,
)


@override_settings(MIGRATION_MODULES={"app": None})
class UserModelTest(TestCase):
    def test_create_user(self):
        User = get_user_model()
        user = User.objects.create_user(
            email_usuario="user@example.com",
            nome_usuario="User",
            password="pass123",
        )
        self.assertEqual(user.email_usuario, "user@example.com")
        self.assertEqual(user.tipo_usuario, "membro_grupo")
        self.assertTrue(user.check_password("pass123"))


@override_settings(MIGRATION_MODULES={"app": None})
class GameConfigModelTest(TestCase):
    def test_default_values(self):
        config = GameConfig.objects.create()
        self.assertEqual(config.capital_inicial, 0)
        self.assertTrue(config.modulo_producao)


@override_settings(MIGRATION_MODULES={"app": None})
class GrupoModelTest(TestCase):
    def test_str(self):
        grupo = Grupo.objects.create(nome="Equipe A")
        self.assertEqual(str(grupo), "Equipe A")


@override_settings(MIGRATION_MODULES={"app": None})
class JogoModelTest(TestCase):
    def test_str(self):
        config = GameConfig.objects.create()
        jogo = Jogo.objects.create(nome="J1", config=config)
        self.assertEqual(str(jogo), "J1")


@override_settings(MIGRATION_MODULES={"app": None})
class InvestimentoModelTest(TestCase):
    def test_str(self):
        grupo = Grupo.objects.create(nome="Equipe B")
        inv = Investimento.objects.create(grupo=grupo, categoria="marketing", valor=1000)
        self.assertIn("Equipe B", str(inv))


@override_settings(MIGRATION_MODULES={"app": None})
class ProdutoMateriaPrimaModelTest(TestCase):
    def test_custo_unitario_estimado(self):
        mp1 = MateriaPrima.objects.create(codigo="MP1", nome="Insumo 1", preco_unitario=3)
        mp2 = MateriaPrima.objects.create(codigo="MP2", nome="Insumo 2", preco_unitario=5)
        produto = Produto.objects.create(codigo="A", nome="Produto A")
        ComposicaoProduto.objects.create(produto=produto, materia_prima=mp1, quantidade_por_unidade=2)
        ComposicaoProduto.objects.create(produto=produto, materia_prima=mp2, quantidade_por_unidade=1)

        self.assertEqual(produto.custo_unitario_estimado, 11)


@override_settings(MIGRATION_MODULES={"app": None})
class CapacidadeProdutoGrupoModelTest(TestCase):
    def test_capacidade_considera_operadores(self):
        grupo = Grupo.objects.create(nome="Grupo Cap")
        produto = Produto.objects.create(codigo="CP", nome="Produto CP", tempo_producao_min=10)
        capacidade = CapacidadeProdutoGrupo.objects.create(
            grupo=grupo,
            produto=produto,
            maquinas=5,
            operadores=4,
            minutos_por_maquina=400,
        )
        # 4 operadores ativam 2 maquinas.
        self.assertEqual(capacidade.capacidade_unidades_rodada, 80)
