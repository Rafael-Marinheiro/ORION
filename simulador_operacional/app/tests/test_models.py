from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from app.models import GameConfig, Grupo, Jogo, Investimento


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
        self.assertTrue(user.check_password("pass123"))


@override_settings(MIGRATION_MODULES={"app": None})
class GameConfigModelTest(TestCase):
    def test_default_values(self):
        config = GameConfig.objects.create()
        self.assertEqual(config.capital_inicial, 1000000)
        self.assertEqual(config.maquinas_iniciais, 40)
        self.assertEqual(config.maquinas_iniciais_a, 15)
        self.assertEqual(config.maquinas_iniciais_b, 15)
        self.assertEqual(config.maquinas_iniciais_c, 10)
        self.assertEqual(config.trabalhadores_iniciais, 80)
        self.assertEqual(config.numero_rodadas, 3)
        self.assertTrue(config.modulo_producao)


@override_settings(MIGRATION_MODULES={"app": None})
class GrupoModelTest(TestCase):
    def test_str(self):
        grupo = Grupo.objects.create(nome="Equipe A")
        self.assertEqual(str(grupo), "Equipe A")

    def test_machine_defaults(self):
        grupo = Grupo.objects.create(nome="Equipe B")
        self.assertEqual(grupo.maquinas_a, 15)
        self.assertEqual(grupo.maquinas_b, 15)
        self.assertEqual(grupo.maquinas_c, 10)


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
