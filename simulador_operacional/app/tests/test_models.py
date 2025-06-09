from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from app.models import GameConfig, Grupo


@override_settings(MIGRATION_MODULES={"app": None})
class UserModelTest(TestCase):
    def test_create_user(self):
        User = get_user_model()
        user = User.objects.create_user(
            email_usuario="user@example.com",
            nome_usuario="User",
            senha_usuario="pass123",
        )
        self.assertEqual(user.email_usuario, "user@example.com")
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
