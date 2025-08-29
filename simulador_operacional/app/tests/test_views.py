from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from app.models import Grupo, Cidade, Investimento, Distribuicao


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
        self.assertRedirects(response, reverse("home"))

    def test_get_logged_in_with_group(self):
        self._create_group(3)
        self.client.login(username="view0@example.com", password="secret")
        response = self.client.get(reverse("painel_grupo"))
        self.assertEqual(response.status_code, 200)

    def test_group_too_small_redirects(self):
        self._create_group(2)
        self.client.login(username="view0@example.com", password="secret")
        response = self.client.get(reverse("painel_grupo"))
        self.assertRedirects(response, reverse("home"))

    def test_group_too_large_redirects(self):
        self._create_group(7)
        self.client.login(username="view0@example.com", password="secret")
        response = self.client.get(reverse("painel_grupo"))
        self.assertRedirects(response, reverse("home"))


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
        self.assertRedirects(response, reverse("home"))

    def test_member_redirect(self):
        response = self.client.post(
            reverse("login"),
            {"username": "membro@example.com", "password": "pass"},
            follow=True,
        )
        self.assertRedirects(response, reverse("home"))


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


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class ProducaoMateriaPrimaTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.ceo = User.objects.create_user(
            email_usuario="ceo@example.com",
            nome_usuario="CEO",
            password="pass",
            tipo_usuario="lider_grupo",
        )
        self.members = [
            User.objects.create_user(
                email_usuario=f"m{i}@example.com",
                nome_usuario=f"M{i}",
                password="pass",
            )
            for i in range(2)
        ]

    def _create_group(self, materia_prima):
        grupo = Grupo.objects.create(nome="G1", capital=1000, materia_prima=materia_prima)
        grupo.membros.add(self.ceo, *self.members)
        return grupo

    def test_producao_sem_materia_prima(self):
        grupo = self._create_group(0)
        self.client.login(username="ceo@example.com", password="pass")
        response = self.client.post(
            reverse("painel_grupo"),
            {
                "rodada": 1,
                "descricao": "Prod",
                "quantidade": 10,
                "enviar_decisao": "",
            },
        )
        self.assertRedirects(response, reverse("painel_grupo"))
        grupo.refresh_from_db()
        self.assertEqual(grupo.estoque, 0)
        self.assertEqual(grupo.materia_prima, 0)

    def test_producao_com_materia_prima(self):
        grupo = self._create_group(20)
        self.client.login(username="ceo@example.com", password="pass")
        response = self.client.post(
            reverse("painel_grupo"),
            {
                "rodada": 1,
                "descricao": "Prod",
                "quantidade": 10,
                "enviar_decisao": "",
            },
        )
        self.assertRedirects(response, reverse("painel_grupo"))
        grupo.refresh_from_db()
        self.assertEqual(grupo.estoque, 10)
        self.assertEqual(grupo.materia_prima, 10)
        self.assertEqual(grupo.capital, 950)


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class MarketingDemandTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.ceo = User.objects.create_user(
            email_usuario="ceo_mark@example.com",
            nome_usuario="CEO",
            password="pass",
            tipo_usuario="lider_grupo",
        )
        self.members = [
            User.objects.create_user(
                email_usuario=f"mkt{i}@example.com",
                nome_usuario=f"Mkt{i}",
                password="pass",
            )
            for i in range(2)
        ]
        self.grupo = Grupo.objects.create(nome="GMarketing", estoque=200, capital=1000)
        self.grupo.membros.add(self.ceo, *self.members)
        self.cidade = Cidade.objects.create(nome="Metropole", distancia_km=10, demanda=100)
        Investimento.objects.create(
            grupo=self.grupo,
            cidade=self.cidade,
            categoria="marketing",
            valor=10000,
        )

    def test_marketing_aumenta_demanda(self):
        self.client.login(username="ceo_mark@example.com", password="pass")
        response = self.client.post(
            reverse("painel_grupo"),
            {
                "cidade": self.cidade.id,
                "rodada": 1,
                "quantidade": 110,
                "preco_unitario": "1",
                "enviar_envio": "",
            },
        )
        self.assertRedirects(response, reverse("painel_grupo"))
        envio = Distribuicao.objects.get()
        self.assertEqual(envio.vendas_realizadas, 110)
        self.assertGreater(envio.fator_marketing, 1)


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class RankingMarketShareTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.staff = User.objects.create_user(
            email_usuario="staff@example.com",
            nome_usuario="Staff",
            password="pass",
            tipo_usuario="gamemaster",
        )
        self.cidade = Cidade.objects.create(nome="C1", distancia_km=10, demanda=1000)
        self.g1 = Grupo.objects.create(nome="G1")
        self.g2 = Grupo.objects.create(nome="G2")
        self.api_client = APIClient()
        self.api_client.force_authenticate(user=self.staff)
        Distribuicao.objects.create(
            grupo=self.g1,
            cidade=self.cidade,
            rodada=1,
            quantidade=100,
            preco_unitario=10,
            custo_transporte=0,
            vendas_realizadas=30,
        )
        Distribuicao.objects.create(
            grupo=self.g2,
            cidade=self.cidade,
            rodada=1,
            quantidade=100,
            preco_unitario=10,
            custo_transporte=0,
            vendas_realizadas=70,
        )

    def test_ranking_view_market_share(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("ranking"))
        grupos = list(response.context["grupos"])
        self.assertEqual(grupos[0].nome, "G2")
        self.assertEqual(grupos[1].nome, "G1")

    def test_ranking_api_market_share(self):
        response = self.api_client.get(reverse("api_ranking"))
        data = response.json()
        self.assertEqual(data[0]["nome"], "G2")
        self.assertEqual(data[1]["nome"], "G1")

