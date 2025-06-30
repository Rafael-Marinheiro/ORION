from django.urls import reverse
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class PainelGrupoViewTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            email_usuario="view@example.com",
            nome_usuario="Viewer",
            password="secret12",
        )

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(reverse("painel_grupo"))
        self.assertEqual(response.status_code, 302)

    def test_get_logged_in(self):
        self.client.login(username="view@example.com", password="secret12")
        response = self.client.get(reverse("painel_grupo"))
        self.assertEqual(response.status_code, 200)


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class LoginRedirectTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user(
            email_usuario="admin@example.com",
            nome_usuario="Admin",
            password="pass1234",
            tipo_usuario="gamemaster",
        )
        self.ceo = User.objects.create_user(
            email_usuario="ceo@example.com",
            nome_usuario="CEO",
            password="pass1234",
            tipo_usuario="lider_grupo",
        )
        self.member = User.objects.create_user(
            email_usuario="membro@example.com",
            nome_usuario="Membro",
            password="pass1234",
            tipo_usuario="membro_grupo",
        )

    def test_admin_redirect(self):
        response = self.client.post(
            reverse("login"),
            {"username": "admin@example.com", "password": "pass1234"},
        )
        self.assertRedirects(response, reverse("game_config"))

    def test_ceo_redirect(self):
        response = self.client.post(
            reverse("login"),
            {"username": "ceo@example.com", "password": "pass1234"},
        )
        self.assertRedirects(response, reverse("painel_grupo"))

    def test_member_redirect(self):
        response = self.client.post(
            reverse("login"),
            {"username": "membro@example.com", "password": "pass1234"},
        )
        self.assertRedirects(response, reverse("painel_grupo"))
