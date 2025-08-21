from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from app.forms import GrupoForm


@override_settings(MIGRATION_MODULES={"app": None})
class GrupoFormTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.users = [
            User.objects.create_user(
                email_usuario=f"u{i}@example.com",
                nome_usuario=f"U{i}",
                password="pass",
            )
            for i in range(6)
        ]

    def _base_data(self):
        return {
            "nome": "G1",
            "capital": 0,
            "estoque": 0,
            "maquinas": 1,
            "maquinas_a": 15,
            "maquinas_b": 15,
            "maquinas_c": 10,
            "trabalhadores": 80,
            "capacidade_maquina": 100,
        }

    def test_invalid_member_count(self):
        data = self._base_data()
        data["membros"] = [u.pk for u in self.users[:2]]
        form = GrupoForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn("membros", form.errors)

    def test_invalid_member_count_too_many(self):
        User = get_user_model()
        extra_user = User.objects.create_user(
            email_usuario="extra@example.com",
            nome_usuario="Extra",
            password="pass",
        )
        data = self._base_data()
        data["membros"] = [u.pk for u in self.users] + [extra_user.pk]
        form = GrupoForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn("membros", form.errors)

    def test_valid_member_count(self):
        data = self._base_data()
        data["membros"] = [u.pk for u in self.users[:3]]
        form = GrupoForm(data)
        self.assertTrue(form.is_valid())
