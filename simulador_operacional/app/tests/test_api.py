from django.urls import reverse
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from app.models import ConsolidadoRodadaGrupo, ExecucaoJob, GameConfig, Grupo, IndicadorRodadaGrupo, Jogo


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class RankingAPITest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            email_usuario="api@example.com",
            nome_usuario="API User",
            password="pass",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        Grupo.objects.create(nome="G1", capital=100)
        Grupo.objects.create(nome="G2", capital=200)

    def test_ranking_order(self):
        response = self.client.get(reverse("api_ranking"))
        self.assertEqual(response.status_code, 200)
        capitals = [g["capital"] for g in response.json()]
        self.assertEqual(capitals, sorted(capitals, reverse=True))


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class RankingMulticriterioAPITest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            email_usuario="api2@example.com",
            nome_usuario="API User 2",
            password="pass",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.g1 = Grupo.objects.create(nome="G1", capital=100)
        self.g2 = Grupo.objects.create(nome="G2", capital=200)
        IndicadorRodadaGrupo.objects.create(
            grupo=self.g1,
            rodada=1,
            score_multicriterio=50,
            lucro_rodada=10,
            market_share_percent=40,
            atendimento_demanda_percent=80,
            eficiencia_estoque_percent=60,
        )
        IndicadorRodadaGrupo.objects.create(
            grupo=self.g2,
            rodada=1,
            score_multicriterio=70,
            lucro_rodada=20,
            market_share_percent=60,
            atendimento_demanda_percent=85,
            eficiencia_estoque_percent=65,
        )

    def test_returns_latest_round_sorted_by_score(self):
        response = self.client.get(reverse("api_ranking_multicriterio"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        scores = [item["score_multicriterio"] for item in data]
        self.assertEqual(scores, sorted(scores, reverse=True))


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class ConsolidadoRodadaAPITest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            email_usuario="api3@example.com",
            nome_usuario="API User 3",
            password="pass",
            tipo_usuario="gamemaster",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.g1 = Grupo.objects.create(nome="G1", capital=100)
        self.g2 = Grupo.objects.create(nome="G2", capital=200)
        ConsolidadoRodadaGrupo.objects.create(
            grupo=self.g1,
            rodada=2,
            receita_vendas=100,
            custos_totais=80,
            lucro_rodada=20,
        )
        ConsolidadoRodadaGrupo.objects.create(
            grupo=self.g2,
            rodada=2,
            receita_vendas=150,
            custos_totais=70,
            lucro_rodada=80,
        )

    def test_endpoint_lista_consolidados(self):
        response = self.client.get("/api/consolidados-rodada/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class MultiJogoIsolationAPITest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            email_usuario="api4@example.com",
            nome_usuario="API User 4",
            password="pass",
            tipo_usuario="membro_grupo",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        config = GameConfig.objects.create()
        jogo1 = Jogo.objects.create(nome="J1", config=config)
        jogo2 = Jogo.objects.create(nome="J2", config=config)
        self.g1 = Grupo.objects.create(nome="GJ1", capital=100, jogo=jogo1)
        self.g2 = Grupo.objects.create(nome="GJ2", capital=200, jogo=jogo2)
        self.g1.membros.add(self.user)
        ConsolidadoRodadaGrupo.objects.create(
            grupo=self.g1,
            rodada=1,
            receita_vendas=10,
            custos_totais=5,
            lucro_rodada=5,
        )
        ConsolidadoRodadaGrupo.objects.create(
            grupo=self.g2,
            rodada=1,
            receita_vendas=20,
            custos_totais=10,
            lucro_rodada=10,
        )

    def test_consolidado_filtra_por_jogo_do_usuario(self):
        response = self.client.get("/api/consolidados-rodada/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertIn("GJ1", response.json()[0]["grupo"])


@override_settings(MIGRATION_MODULES={"app": None}, SECURE_SSL_REDIRECT=False)
class JobsEndpointAPITest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            email_usuario="api5@example.com",
            nome_usuario="API User 5",
            password="pass",
            tipo_usuario="gamemaster",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        ExecucaoJob.objects.create(comando="fechar_rodadas", correlation_id="abc123", status="sucesso")

    def test_jobs_endpoint(self):
        response = self.client.get("/api/execucoes-jobs/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
