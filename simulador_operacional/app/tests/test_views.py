from django.urls import reverse
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from app.models import Grupo


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class PainelGrupoViewTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.users = [
            User.objects.create_user(
                email_usuario=f"view{i}@example.com",
                nome_usuario=f"Viewer{i}",
                password="secret",
            )
            for i in range(7)
        ]
        self.user = self.users[0]

    def _create_group(self, count):
        grupo = Grupo.objects.create(nome="G1")
        for u in self.users[:count]:
            grupo.membros.add(u)
        return grupo

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(reverse("painel_grupo"))
        self.assertEqual(response.status_code, 302)

    def test_redirect_if_no_group(self):
        self.client.login(username="view0@example.com", password="secret")
        response = self.client.get(reverse("painel_grupo"))
        self.assertRedirects(response, reverse("criar_grupo"))

    def test_get_logged_in_with_group(self):
        self._create_group(3)
        self.client.login(username="view0@example.com", password="secret")
        response = self.client.get(reverse("painel_grupo"))
        self.assertEqual(response.status_code, 200)

    def test_group_too_small_redirects(self):
        self._create_group(2)
        self.client.login(username="view0@example.com", password="secret")
        response = self.client.get(reverse("painel_grupo"))
        self.assertRedirects(response, reverse("criar_grupo"))

    def test_group_too_large_redirects(self):
        self._create_group(7)
        self.client.login(username="view0@example.com", password="secret")
        response = self.client.get(reverse("painel_grupo"))
        self.assertRedirects(response, reverse("criar_grupo"))


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class LoginRedirectTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user(
            email_usuario="admin@example.com",
            nome_usuario="Admin",
            password="pass",
            tipo_usuario="gamemaster",
        )
        self.ceo = User.objects.create_user(
            email_usuario="ceo@example.com",
            nome_usuario="CEO",
            password="pass",
            tipo_usuario="lider_grupo",
        )
        self.member = User.objects.create_user(
            email_usuario="membro@example.com",
            nome_usuario="Membro",
            password="pass",
            tipo_usuario="membro_grupo",
        )

    def test_admin_redirect(self):
        response = self.client.post(
            reverse("login"),
            {"username": "admin@example.com", "password": "pass"},
        )
        self.assertRedirects(response, reverse("game_config"))

    def test_ceo_redirect(self):
        response = self.client.post(
            reverse("login"),
            {"username": "ceo@example.com", "password": "pass"},
            follow=True,
        )
        self.assertRedirects(response, reverse("criar_grupo"))

    def test_member_redirect(self):
        response = self.client.post(
            reverse("login"),
            {"username": "membro@example.com", "password": "pass"},
            follow=True,
        )
        self.assertRedirects(response, reverse("criar_grupo"))


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class RegisterViewAccessTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.gm = User.objects.create_user(
            email_usuario="gm@example.com",
            nome_usuario="GM",
            password="pass",
            tipo_usuario="gamemaster",
        )
        self.ceo = User.objects.create_user(
            email_usuario="ceo2@example.com",
            nome_usuario="CEO",
            password="pass",
            tipo_usuario="lider_grupo",
        )

    def test_gamemaster_can_access(self):
        self.client.login(username="gm@example.com", password="pass")
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)

    def test_non_gamemaster_forbidden(self):
        self.client.login(username="ceo2@example.com", password="pass")
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 403)

